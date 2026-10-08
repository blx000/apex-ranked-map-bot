from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage

from apex_bot.database import SubscriberStore
from apex_bot.models import RankedRotation
from apex_bot.notifier import RotationNotifier


class FakeApexClient:
    def __init__(self, rotation: RankedRotation) -> None:
        self.rotation = rotation
        self.calls = 0

    async def get_ranked_rotation(self) -> RankedRotation:
        self.calls += 1
        return self.rotation


class FakeBot:
    def __init__(self, *, forbidden_chat_id: int | None = None) -> None:
        self.forbidden_chat_id = forbidden_chat_id
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs: Any) -> None:
        if chat_id == self.forbidden_chat_id:
            raise TelegramForbiddenError(
                method=SendMessage(chat_id=chat_id, text=text),
                message="bot was blocked by the user",
            )
        self.sent.append((chat_id, text))


@pytest.mark.asyncio
async def test_new_rotation_is_delivered_once(tmp_path: Path, rotation: RankedRotation) -> None:
    store = SubscriberStore(str(tmp_path / "bot.db"))
    await store.open()
    try:
        await store.subscribe(1, "old-rotation")
        await store.subscribe(2, rotation.key)
        bot = FakeBot()
        notifier = RotationNotifier(bot, FakeApexClient(rotation), store, max_send_attempts=1)  # type: ignore[arg-type]

        await notifier.check_once()
        await notifier.check_once()

        assert [chat_id for chat_id, _ in bot.sent] == [1]
        assert "E-District (Квартал Электро)" in bot.sent[0][1]
        assert await store.pending_subscribers(rotation.key) == []
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_same_map_in_new_time_slot_is_new_rotation(
    tmp_path: Path, rotation_payload: dict[str, object]
) -> None:
    first = RankedRotation.from_payload(rotation_payload)
    ranked = rotation_payload["ranked"]
    assert isinstance(ranked, dict)
    current = ranked["current"]
    assert isinstance(current, dict)
    current["start"] = 2_000_032_400
    current["end"] = 2_000_048_600
    second = RankedRotation.from_payload(rotation_payload)
    assert first.current.name == second.current.name
    assert first.key != second.key


@pytest.mark.asyncio
async def test_blocked_user_is_deactivated(tmp_path: Path, rotation: RankedRotation) -> None:
    store = SubscriberStore(str(tmp_path / "bot.db"))
    await store.open()
    try:
        await store.subscribe(99, "old-rotation")
        bot = FakeBot(forbidden_chat_id=99)
        notifier = RotationNotifier(bot, FakeApexClient(rotation), store, max_send_attempts=1)  # type: ignore[arg-type]

        await notifier.check_once()

        subscriber = await store.get(99)
        assert subscriber is not None
        assert subscriber["active"] == 0
    finally:
        await store.close()


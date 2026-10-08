from __future__ import annotations

from pathlib import Path

import pytest

from apex_bot.database import SubscriberStore


@pytest.mark.asyncio
async def test_subscribe_is_idempotent_and_stop_disables(tmp_path: Path) -> None:
    store = SubscriberStore(str(tmp_path / "bot.db"))
    await store.open()
    try:
        await store.subscribe(101, "rotation-a")
        await store.subscribe(101, "rotation-a")
        assert await store.pending_subscribers("rotation-a") == []

        assert await store.unsubscribe(101) is True
        assert await store.unsubscribe(101) is False
        subscriber = await store.get(101)
        assert subscriber is not None
        assert subscriber["active"] == 0
    finally:
        await store.close()


@pytest.mark.asyncio
async def test_subscription_survives_reopen(tmp_path: Path) -> None:
    database_path = str(tmp_path / "persistent.db")
    first = SubscriberStore(database_path)
    await first.open()
    await first.subscribe(202, "rotation-a")
    await first.close()

    second = SubscriberStore(database_path)
    await second.open()
    try:
        assert await second.pending_subscribers("rotation-a") == []
        assert await second.pending_subscribers("rotation-b") == [202]
        await second.mark_notified(202, "rotation-b")
        assert await second.pending_subscribers("rotation-b") == []
    finally:
        await second.close()


@pytest.mark.asyncio
async def test_failed_initial_snapshot_remains_pending(tmp_path: Path) -> None:
    store = SubscriberStore(str(tmp_path / "bot.db"))
    await store.open()
    try:
        await store.subscribe(303, None)
        assert await store.pending_subscribers("first-known-rotation") == [303]
    finally:
        await store.close()


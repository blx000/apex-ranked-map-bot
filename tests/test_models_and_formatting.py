from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apex_bot.formatting import format_duration, format_rotation
from apex_bot.models import RankedRotation, RotationDataError


def test_parse_ranked_rotation_and_key(rotation_payload: dict[str, object]) -> None:
    rotation = RankedRotation.from_payload(rotation_payload)

    assert rotation.current.name == "E-District"
    assert rotation.next.name == "World's Edge"
    assert rotation.key == "2000000000:2000016200:district_rotation"


def test_remaining_time_uses_end_timestamp(rotation: RankedRotation) -> None:
    now = datetime.fromtimestamp(2_000_012_540, tz=timezone.utc)
    assert rotation.remaining_seconds(now) == 3_660


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "меньше минуты"),
        (59, "меньше минуты"),
        (60, "1 мин"),
        (3_600, "1 ч"),
        (3_660, "1 ч 1 мин"),
        (16_199, "4 ч 29 мин"),
    ],
)
def test_format_duration(seconds: int, expected: str) -> None:
    assert format_duration(seconds) == expected


def test_rotation_message_contains_translations_and_attribution(rotation: RankedRotation) -> None:
    message = format_rotation(rotation, changed=True)

    assert "E-District (Квартал Электро)" in message
    assert "World's Edge (Край света)" in message
    assert "Карта в Ranked сменилась" in message
    assert "Data provided by Apex Legends Status" in message


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"ranked": {}},
        {"ranked": {"current": {}, "next": {}}},
        {
            "ranked": {
                "current": {"map": "Olympus", "start": 20, "end": 10},
                "next": {"map": "Storm Point", "start": 20, "end": 30},
            }
        },
    ],
)
def test_invalid_payload_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(RotationDataError):
        RankedRotation.from_payload(payload)

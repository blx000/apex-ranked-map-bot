from __future__ import annotations

import pytest

from apex_bot.models import RankedRotation


@pytest.fixture
def rotation_payload() -> dict[str, object]:
    return {
        "ranked": {
            "current": {
                "start": 2_000_000_000,
                "end": 2_000_016_200,
                "map": "E-District",
                "code": "district_rotation",
            },
            "next": {
                "start": 2_000_016_200,
                "end": 2_000_032_400,
                "map": "World's Edge",
                "code": "worlds_edge_rotation",
            },
        }
    }


@pytest.fixture
def rotation(rotation_payload: dict[str, object]) -> RankedRotation:
    return RankedRotation.from_payload(rotation_payload)


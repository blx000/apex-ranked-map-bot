from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


class RotationDataError(ValueError):
    """Raised when the Apex API response has no usable ranked rotation."""


@dataclass(frozen=True, slots=True)
class MapWindow:
    name: str
    start: int
    end: int
    code: str

    @classmethod
    def from_payload(cls, value: Any, *, field: str) -> "MapWindow":
        if not isinstance(value, Mapping):
            raise RotationDataError(f"{field} must be an object")

        name = value.get("map")
        start = value.get("start")
        end = value.get("end")
        if not isinstance(name, str) or not name.strip():
            raise RotationDataError(f"{field}.map must be a non-empty string")
        if isinstance(start, bool) or not isinstance(start, (int, float)):
            raise RotationDataError(f"{field}.start must be a Unix timestamp")
        if isinstance(end, bool) or not isinstance(end, (int, float)):
            raise RotationDataError(f"{field}.end must be a Unix timestamp")
        if int(end) <= int(start):
            raise RotationDataError(f"{field}.end must be later than start")

        raw_code = value.get("code")
        code = raw_code.strip() if isinstance(raw_code, str) else name.strip()
        return cls(name=name.strip(), start=int(start), end=int(end), code=code)


@dataclass(frozen=True, slots=True)
class RankedRotation:
    current: MapWindow
    next: MapWindow

    @property
    def key(self) -> str:
        return f"{self.current.start}:{self.current.end}:{self.current.code}"

    def remaining_seconds(self, now: datetime | None = None) -> int:
        current_time = now or datetime.now(timezone.utc)
        return max(0, self.current.end - int(current_time.timestamp()))

    @classmethod
    def from_payload(cls, payload: Any) -> "RankedRotation":
        if not isinstance(payload, Mapping):
            raise RotationDataError("API response must be an object")

        ranked = None
        for key in ("ranked", "battle_royale_ranked", "battleRoyaleRanked"):
            candidate = payload.get(key)
            if isinstance(candidate, Mapping):
                ranked = candidate
                break
        if ranked is None:
            raise RotationDataError("API response does not contain ranked rotation")

        return cls(
            current=MapWindow.from_payload(ranked.get("current"), field="ranked.current"),
            next=MapWindow.from_payload(ranked.get("next"), field="ranked.next"),
        )


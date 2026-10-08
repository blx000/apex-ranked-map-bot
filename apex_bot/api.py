from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from apex_bot.models import RankedRotation, RotationDataError

logger = logging.getLogger(__name__)


class ApexAPIError(RuntimeError):
    """Raised when the Apex map rotation cannot be retrieved."""


class ApexClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.apexlegendsstatus.com",
        timeout_seconds: float = 10.0,
        max_attempts: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_attempts = max_attempts
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout_seconds)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_ranked_rotation(self) -> RankedRotation:
        last_error: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                response = await self._client.get(
                    f"{self._base_url}/maprotation",
                    params={"version": 2},
                    headers={"Authorization": self._api_key},
                )
                response.raise_for_status()
                payload: Any = response.json()
                return RankedRotation.from_payload(payload)
            except (httpx.HTTPError, ValueError, RotationDataError) as exc:
                last_error = exc
                retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code in {
                    400,
                    405,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if not retryable or attempt == self._max_attempts:
                    break
                delay = 2 ** (attempt - 1)
                logger.warning("Apex API request failed; retrying", extra={"attempt": attempt, "delay": delay})
                await asyncio.sleep(delay)

        raise ApexAPIError("Не удалось получить ротацию карт Apex Legends") from last_error


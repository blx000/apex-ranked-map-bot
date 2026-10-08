from __future__ import annotations

import httpx
import pytest
import respx

from apex_bot.api import ApexAPIError, ApexClient


@pytest.mark.asyncio
@respx.mock
async def test_api_uses_auth_header_and_version_two(rotation_payload: dict[str, object]) -> None:
    route = respx.get("https://api.apexlegendsstatus.com/maprotation").mock(
        return_value=httpx.Response(200, json=rotation_payload)
    )
    client = ApexClient("secret-key", max_attempts=1)
    try:
        rotation = await client.get_ranked_rotation()
    finally:
        await client.close()

    request = route.calls.last.request
    assert request.headers["Authorization"] == "secret-key"
    assert request.url.params["version"] == "2"
    assert rotation.current.name == "E-District"


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("status_code", [403, 429, 500])
async def test_api_http_errors_are_wrapped(status_code: int) -> None:
    respx.get("https://api.apexlegendsstatus.com/maprotation").mock(
        return_value=httpx.Response(status_code, json={"error": "failure"})
    )
    client = ApexClient("secret-key", max_attempts=1)
    try:
        with pytest.raises(ApexAPIError):
            await client.get_ranked_rotation()
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_invalid_json_is_wrapped() -> None:
    respx.get("https://api.apexlegendsstatus.com/maprotation").mock(
        return_value=httpx.Response(200, text="not-json")
    )
    client = ApexClient("secret-key", max_attempts=1)
    try:
        with pytest.raises(ApexAPIError):
            await client.get_ranked_rotation()
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_timeout_is_wrapped() -> None:
    respx.get("https://api.apexlegendsstatus.com/maprotation").mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    client = ApexClient("secret-key", max_attempts=1)
    try:
        with pytest.raises(ApexAPIError):
            await client.get_ranked_rotation()
    finally:
        await client.close()


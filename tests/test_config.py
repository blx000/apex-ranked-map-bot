from __future__ import annotations

import pytest

from apex_bot.config import ConfigError, Settings


def test_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-secret")
    monkeypatch.setenv("APEX_API_KEY", "apex-secret")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "75")
    monkeypatch.setenv("DATABASE_PATH", "/tmp/apex.db")

    settings = Settings.from_env()

    assert settings.telegram_bot_token == "telegram-secret"
    assert settings.apex_api_key == "apex-secret"
    assert settings.poll_interval_seconds == 75
    assert settings.database_path == "/tmp/apex.db"


def test_required_secrets_are_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("APEX_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        Settings.from_env()


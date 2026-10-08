from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(ValueError):
    """Raised when required application configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    apex_api_key: str
    database_path: str = "/app/data/bot.db"
    poll_interval_seconds: int = 60
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        apex_api_key = os.getenv("APEX_API_KEY", "").strip()
        if not telegram_token:
            raise ConfigError("TELEGRAM_BOT_TOKEN is required")
        if not apex_api_key:
            raise ConfigError("APEX_API_KEY is required")

        raw_interval = os.getenv("POLL_INTERVAL_SECONDS", "60")
        try:
            interval = int(raw_interval)
        except ValueError as exc:
            raise ConfigError("POLL_INTERVAL_SECONDS must be an integer") from exc
        if interval < 10:
            raise ConfigError("POLL_INTERVAL_SECONDS must be at least 10")

        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigError("LOG_LEVEL must be a standard Python log level")

        return cls(
            telegram_bot_token=telegram_token,
            apex_api_key=apex_api_key,
            database_path=os.getenv("DATABASE_PATH", "/app/data/bot.db"),
            poll_interval_seconds=interval,
            log_level=log_level,
        )


from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)

from apex_bot.api import ApexAPIError, ApexClient
from apex_bot.database import SubscriberStore
from apex_bot.formatting import format_rotation
from apex_bot.handlers import refresh_keyboard

logger = logging.getLogger(__name__)


class RotationNotifier:
    def __init__(
        self,
        bot: Bot,
        apex: ApexClient,
        store: SubscriberStore,
        *,
        interval_seconds: int = 60,
        max_send_attempts: int = 3,
    ) -> None:
        self._bot = bot
        self._apex = apex
        self._store = store
        self._interval_seconds = interval_seconds
        self._max_send_attempts = max_send_attempts
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        self._stop_event.set()

    async def run(self) -> None:
        logger.info("Rotation notifier started", extra={"interval_seconds": self._interval_seconds})
        while not self._stop_event.is_set():
            try:
                await self.check_once()
            except Exception:
                logger.exception("Unexpected error in rotation notifier")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval_seconds)
            except TimeoutError:
                pass
        logger.info("Rotation notifier stopped")

    async def check_once(self) -> None:
        try:
            rotation = await self._apex.get_ranked_rotation()
        except ApexAPIError:
            logger.exception("Apex API unavailable; notification cycle skipped")
            return

        chat_ids = await self._store.pending_subscribers(rotation.key)
        if not chat_ids:
            return

        logger.info(
            "New rotation detected for subscribers",
            extra={"rotation_key": rotation.key, "subscriber_count": len(chat_ids)},
        )
        message = format_rotation(rotation, changed=True)
        for chat_id in chat_ids:
            outcome = await self._send_with_retry(chat_id, message)
            if outcome == "sent":
                await self._store.mark_notified(chat_id, rotation.key)
            elif outcome == "forbidden":
                await self._store.deactivate(chat_id)

    async def _send_with_retry(self, chat_id: int, text: str) -> str:
        for attempt in range(1, self._max_send_attempts + 1):
            try:
                await self._bot.send_message(chat_id, text, reply_markup=refresh_keyboard())
                return "sent"
            except TelegramForbiddenError:
                logger.info("Subscriber blocked the bot; deactivating", extra={"chat_id": chat_id})
                return "forbidden"
            except TelegramRetryAfter as exc:
                if attempt == self._max_send_attempts:
                    break
                delay = max(float(exc.retry_after), 1.0)
                logger.warning(
                    "Telegram rate limit; retrying",
                    extra={"chat_id": chat_id, "attempt": attempt, "delay": delay},
                )
                await asyncio.sleep(delay)
            except (TelegramNetworkError, TelegramServerError):
                if attempt == self._max_send_attempts:
                    break
                delay = float(2 ** (attempt - 1))
                logger.warning(
                    "Transient Telegram error; retrying",
                    extra={"chat_id": chat_id, "attempt": attempt, "delay": delay},
                )
                await asyncio.sleep(delay)
            except TelegramAPIError:
                logger.exception("Telegram rejected notification", extra={"chat_id": chat_id})
                return "failed"

        logger.error("Telegram notification retries exhausted", extra={"chat_id": chat_id})
        return "failed"


from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from apex_bot.api import ApexClient
from apex_bot.config import ConfigError, Settings
from apex_bot.database import SubscriberStore
from apex_bot.handlers import create_router
from apex_bot.logging_config import configure_logging
from apex_bot.notifier import RotationNotifier

logger = logging.getLogger(__name__)


async def main(settings: Settings) -> None:
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
    )
    dispatcher = Dispatcher()
    store = SubscriberStore(settings.database_path)
    apex = ApexClient(settings.apex_api_key)
    notifier = RotationNotifier(
        bot,
        apex,
        store,
        interval_seconds=settings.poll_interval_seconds,
    )

    await store.open()
    dispatcher.include_router(create_router(apex, store))
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Включить уведомления"),
            BotCommand(command="map", description="Текущая и следующая карта"),
            BotCommand(command="stop", description="Отключить уведомления"),
            BotCommand(command="help", description="Справка"),
        ]
    )
    await bot.delete_webhook(drop_pending_updates=False)

    notifier_task = asyncio.create_task(notifier.run(), name="rotation-notifier")
    logger.info("Telegram bot started")
    try:
        await dispatcher.start_polling(bot)
    finally:
        notifier.stop()
        await notifier_task
        await apex.close()
        await store.close()
        await bot.session.close()
        logger.info("Telegram bot stopped")


def run() -> None:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        configure_logging("INFO")
        logger.critical("Invalid configuration", extra={"error": str(exc)})
        raise SystemExit(2) from exc

    configure_logging(settings.log_level)
    asyncio.run(main(settings))


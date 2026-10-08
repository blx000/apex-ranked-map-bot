from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from apex_bot.api import ApexAPIError, ApexClient
from apex_bot.database import SubscriberStore
from apex_bot.formatting import format_rotation

logger = logging.getLogger(__name__)

REFRESH_CALLBACK = "refresh_map"


def refresh_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=REFRESH_CALLBACK)],
        ]
    )


def create_router(apex: ApexClient, store: SubscriberStore) -> Router:
    router = Router(name="commands")

    async def send_rotation(message: Message, *, edit: bool = False) -> None:
        try:
            rotation = await apex.get_ranked_rotation()
        except ApexAPIError:
            logger.exception("Failed to load rotation for Telegram command")
            error_text = "⚠️ Сейчас не удалось получить ротацию. Попробуйте ещё раз немного позже."
            if edit:
                await message.edit_text(error_text, reply_markup=refresh_keyboard())
            else:
                await message.answer(error_text, reply_markup=refresh_keyboard())
            return

        text = format_rotation(rotation)
        if edit:
            try:
                await message.edit_text(text, reply_markup=refresh_keyboard())
            except TelegramBadRequest as exc:
                # A refresh inside the same minute often produces identical text.
                if "message is not modified" not in exc.message.casefold():
                    raise
        else:
            await message.answer(text, reply_markup=refresh_keyboard())

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        try:
            rotation = await apex.get_ranked_rotation()
        except ApexAPIError:
            logger.exception("Failed to load rotation while subscribing", extra={"chat_id": message.chat.id})
            await store.subscribe(message.chat.id, None)
            await message.answer(
                "✅ Вы подписаны на уведомления.\n\n"
                "⚠️ Текущую карту пока получить не удалось — бот попробует снова автоматически.",
                reply_markup=refresh_keyboard(),
            )
            return

        await store.subscribe(message.chat.id, rotation.key)
        await message.answer(
            "✅ Вы подписаны на уведомления о смене карты.\n\n" + format_rotation(rotation),
            reply_markup=refresh_keyboard(),
        )

    @router.message(Command("map"))
    async def current_map(message: Message) -> None:
        await send_rotation(message)

    @router.message(Command("stop"))
    async def stop(message: Message) -> None:
        was_active = await store.unsubscribe(message.chat.id)
        text = (
            "🔕 Уведомления отключены. Чтобы включить их снова, отправьте /start."
            if was_active
            else "Уведомления уже отключены. Чтобы подписаться, отправьте /start."
        )
        await message.answer(text)

    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer(
            "Я слежу за ротацией карт в рейтинговом режиме Apex Legends.\n\n"
            "/start — включить уведомления\n"
            "/map — узнать текущую и следующую карту\n"
            "/stop — отключить уведомления\n"
            "/help — показать эту справку"
        )

    @router.callback_query(F.data == REFRESH_CALLBACK)
    async def refresh(callback: CallbackQuery) -> None:
        await callback.answer("Обновляю…")
        if callback.message is not None:
            await send_rotation(callback.message, edit=True)

    return router

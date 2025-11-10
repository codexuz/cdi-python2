# bot/app/bot.py
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import settings
from .handlers import common, auth


def build_bot() -> Bot:
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(auth.router)
    dp.include_router(common.router)
    return dp

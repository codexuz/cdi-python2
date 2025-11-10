#  bot/app/keyboards.py
from __future__ import annotations
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📲 Register code"), KeyboardButton(text="🔐 Login code")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb, resize_keyboard=True, one_time_keyboard=False
    )

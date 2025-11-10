# bot/app/handlers/common.py
from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import CommandStart, Command

from ..keyboards import main_menu

router = Router(name="common")


@router.message(CommandStart())
async def start_cmd(msg: types.Message) -> None:
    await msg.answer(
        "👋 Assalomu alaykum!\n\n"
        "Men *CDI IELTS* rasmiy botiman. "
        "Bu bot orqali siz ro‘yxatdan o‘tish yoki tizimga kirish uchun zarur bo‘lgan kodni olishingiz mumkin.\n\n"
        "Quyidagi menyudan kerakli bo‘limni tanlang:",
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def help_cmd(msg: types.Message) -> None:
    await msg.answer(
        "ℹ️ *Yordam bo‘limi*\n\n"
        "Botdan foydalanish bo‘yicha qo‘llanma:\n"
        "1️⃣ /start — asosiy menyuni ochadi\n"
        "2️⃣ 📲 *Register code* — yangi foydalanuvchi sifatida ro‘yxatdan o‘tish OTP kodini olasiz\n"
        "3️⃣ 🔐 *Login code* — tizimga kirish uchun OTP kodini olasiz\n\n"
        "❗ Diqqat: Kod 2 daqiqa davomida amal qiladi.",
        parse_mode="Markdown",
    )


@router.message()
async def fallback_cmd(msg: types.Message) -> None:
    await msg.answer(
        "⚠️ Noma’lum buyruq.\n\n"
        "Menyu uchun 👉 /start ni yozing yoki tugmalardan foydalaning."
    )

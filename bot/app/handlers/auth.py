# bot/app/handlers/auth.py
from __future__ import annotations

import logging
import time
from aiogram import Router, types, F

from ..otp import generate_otp
from ..api import backend_client
from ..otp_cache import get_code, set_code

router = Router(name="auth")
log = logging.getLogger(__name__)

REGISTER_BTN = "📲 Register code"
LOGIN_BTN = "🔐 Login code"

REGISTER_ALIASES = [
    REGISTER_BTN,
    "Register code",
    "📲Register code",
    "Register code📲",
]
LOGIN_ALIASES = [
    LOGIN_BTN,
    "Login code",
    "🔐Login code",
    "Login code🔐",
]

_last_press: dict[int, float] = {}
DEBOUNCE_SEC = 2


def _debounced(user_id: int) -> bool:
    now = time.time()
    last = _last_press.get(user_id, 0)
    _last_press[user_id] = now
    return (now - last) < DEBOUNCE_SEC


async def _handle_purpose(msg: types.Message, purpose: str) -> None:
    if not msg.from_user:
        await msg.answer("Telegram foydalanuvchi ma’lumoti yo‘q.")
        return
    if _debounced(msg.from_user.id):
        return

    tg_id = msg.from_user.id
    tg_username = msg.from_user.username or ""

    try:
        status = await backend_client.get_otp_status(
            telegram_id=tg_id, telegram_username=tg_username, purpose=purpose
        )
    except Exception as e:
        log.exception("Status check failed: %s", e)
        await msg.answer("❌ Server bilan aloqa xatosi. Keyinroq urinib ko‘ring.")
        return

    active = bool(status.get("active"))
    remaining = int(status.get("remaining_seconds") or 0)

    if active and remaining > 0:
        cached = get_code(tg_id, purpose)
        if cached:
            code, rem = cached
            await msg.answer(
                f"✅ {purpose.title()} OTP (aktiv): *{code}*\n"
                f"Qolgan vaqt: {rem} soniya.",
                parse_mode="Markdown",
            )
        else:
            await msg.answer(
                f"ℹ️ Bu tur uchun aktiv kod bor.\nQolgan vaqt: {remaining} soniya."
            )
        return

    new_code = generate_otp()
    try:
        r = await backend_client.push_otp(
            telegram_id=tg_id,
            telegram_username=tg_username,
            code=new_code,
            purpose=purpose,
        )
    except Exception as e:
        log.exception("OTP ingest failed: %s", e)
        await msg.answer("❌ Kodni saqlashda xatolik. Keyinroq urinib ko‘ring.")
        return

    if r.status_code == 201:
        set_code(tg_id, purpose, new_code, ttl_seconds=120)
        await msg.answer(
            f"✅ {purpose.title()} OTP: *{new_code}*\n"
            "Kod 2 daqiqa ichida amal qiladi.\n"
            "Iltimos, ilovadagi mos oynaga kodni kiriting.",
            parse_mode="Markdown",
        )
        return

    if r.status_code == 409:
        try:
            status = await backend_client.get_otp_status(
                telegram_id=tg_id, telegram_username=tg_username, purpose=purpose
            )
            remaining = int(status.get("remaining_seconds") or 0)
        except Exception:
            remaining = 0
        await msg.answer(
            "⚠️ Aktiv kod allaqachon mavjud.\n"
            + (f"Qolgan vaqt: {remaining} soniya." if remaining else "")
        )
        return

    await msg.answer("❌ Kutilmagan xatolik.")


@router.message(F.text.in_(REGISTER_ALIASES))
async def register_code(msg: types.Message) -> None:
    await _handle_purpose(msg, "register")


@router.message(F.text.in_(LOGIN_ALIASES))
async def login_code(msg: types.Message) -> None:
    await _handle_purpose(msg, "login")

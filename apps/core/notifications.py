# apps/core/notifications.py
import logging
import httpx
from django.conf import settings

log = logging.getLogger(__name__)


async def _tg_send_async(text: str, chat_id: str):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not chat_id or not text:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    timeout = httpx.Timeout(connect=3.0, read=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()


def notify_telegram_admin_sync(text: str):

    try:
        import anyio

        anyio.run(_tg_send_async, text, settings.TELEGRAM_ADMIN_CHAT_ID)
    except Exception as e:
        log.warning("Telegram notify failed: %s", e)

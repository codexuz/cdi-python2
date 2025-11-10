# bot/app/main.py
from __future__ import annotations
import asyncio
import uvloop
import logging

from .logger import setup_logging
from .bot import build_bot, build_dispatcher
from .api import backend_client
from .health import start_health_server


async def _main() -> None:
    setup_logging()
    log = logging.getLogger("bot.main")

    bot = build_bot()
    dp = build_dispatcher()

    asyncio.create_task(start_health_server())

    await bot.delete_webhook(drop_pending_updates=True)

    log.info("Starting polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        await backend_client.close()
        await bot.session.close()
        log.info("Bot stopped.")


def main() -> None:
    uvloop.install()
    asyncio.run(_main())


if __name__ == "__main__":
    main()

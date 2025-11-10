#  bot/app/health.py
from __future__ import annotations

from aiohttp import web

from .config import settings


async def handle_health(_request: web.Request) -> web.Response:
    return web.Response(text="healthy\n")


async def start_health_server() -> None:
    app = web.Application()
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    # Use bot_port if available, otherwise fall back to health_port
    port = getattr(settings, 'bot_port', settings.health_port)
    site = web.TCPSite(runner, settings.health_host, port)
    await site.start()

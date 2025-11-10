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
    site = web.TCPSite(runner, settings.health_host, settings.health_port)
    await site.start()

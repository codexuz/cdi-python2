# bot/app/api.py
from __future__ import annotations

import os
from typing import Any

import httpx

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://web:8000")
INGEST_TOKEN = os.getenv("BOT_INGEST_TOKEN")


class BackendClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=10.0)
        self._hdr = {"X-Bot-Token": INGEST_TOKEN or ""}

    async def close(self) -> None:
        await self._client.aclose()

    async def get_otp_status(
        self, *, telegram_id: int, telegram_username: str, purpose: str
    ) -> dict[str, Any]:
        r = await self._client.get(
            "/api/accounts/otp/status/",
            headers=self._hdr,
            params={
                "telegram_id": telegram_id,
                "telegram_username": telegram_username or "",
                "purpose": purpose,
            },
        )
        r.raise_for_status()
        return r.json()

    async def push_otp(
        self, *, telegram_id: int, telegram_username: str, code: str, purpose: str
    ) -> httpx.Response:
        r = await self._client.post(
            "/api/accounts/otp/ingest/",
            headers=self._hdr,
            json={
                "telegram_id": telegram_id,
                "telegram_username": telegram_username or "",
                "code": code,
                "purpose": purpose,
            },
        )
        if r.status_code not in (201, 409):
            r.raise_for_status()
        return r


backend_client = BackendClient()

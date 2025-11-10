# bot/app/otp_cache.py
from __future__ import annotations

import time
from typing import Optional, Tuple

_store: dict[tuple[int, str], tuple[str, float]] = {}


def set_code(telegram_id: int, purpose: str, code: str, ttl_seconds: int) -> None:
    _store[(telegram_id, purpose)] = (code, time.time() + ttl_seconds)


def get_code(telegram_id: int, purpose: str) -> Optional[Tuple[str, int]]:
    data = _store.get((telegram_id, purpose))
    if not data:
        return None
    code, exp = data
    remaining = int(exp - time.time())
    if remaining <= 0:
        _store.pop((telegram_id, purpose), None)
        return None
    return code, remaining


def clear_expired() -> None:
    now = time.time()
    for k, (_, exp) in list(_store.items()):
        if exp <= now:
            _store.pop(k, None)

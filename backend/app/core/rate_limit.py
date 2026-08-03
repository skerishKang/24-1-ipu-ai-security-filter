from __future__ import annotations

import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.auth import API_KEY_HEADER_NAME, hash_api_key


def rate_limit_key() -> str:
    return os.getenv("IPU_RATE_LIMIT_KEY", "remote_address").strip().lower() or "remote_address"


def rate_limit_key_func():
    key_kind = rate_limit_key()
    if key_kind == "api_key":
        def key_func(request: Request) -> str:
            api_key = request.headers.get(API_KEY_HEADER_NAME, "")
            return hash_api_key(api_key) if api_key else "anonymous"
        return key_func
    return get_remote_address


limiter = Limiter(key_func=rate_limit_key_func())

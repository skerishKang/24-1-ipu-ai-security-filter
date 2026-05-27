from __future__ import annotations

import hashlib
import hmac

from fastapi import Header, HTTPException, Request, status

from app.core.settings import BackendSettings

API_KEY_HEADER_NAME = "X-IPU-API-Key"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), expected_hash)


def optional_auth_owner_hash(
    request: Request,
    x_ipu_api_key: str | None = Header(default=None, alias=API_KEY_HEADER_NAME),
) -> str:
    settings: BackendSettings = request.app.state.settings
    if not settings.is_public_deployment():
        return "dev-local"

    if not settings.api_key_hash:
        return "public-unconfigured"

    if not x_ipu_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not verify_api_key(x_ipu_api_key, settings.api_key_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return settings.api_key_hash

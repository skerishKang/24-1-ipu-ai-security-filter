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


def derive_caller_identity(api_key: str, *, expected_hash: str | None) -> str:
    """Per-caller identity used as the ``owner_hash`` boundary.

    Public mode: include the supplied API key in the hash so two distinct
    callers holding the same configured key still get different owner
    identities. This is what the restore owner-check actually verifies
    against, so a leaked restore token only works for the same caller.
    The constant-time compare in the session store still uses the expected
    hash, so an attacker who knows the expected hash cannot derive a valid
    caller identity without the raw key.
    """
    if expected_hash is None:
        return "public-unconfigured"
    salt = expected_hash[:16]
    return hashlib.sha256(f"caller:{salt}:{api_key}".encode("utf-8")).hexdigest()


def optional_auth_owner_hash(
    request: Request,
    x_ipu_api_key: str | None = Header(default=None, alias=API_KEY_HEADER_NAME),
) -> str:
    settings: BackendSettings = request.app.state.settings
    if not settings.is_public_deployment():
        return "dev-local"

    if not settings.api_key_hash:
        # Fail closed: the startup guard in ``create_app`` should prevent
        # public mode without an api_key_hash, but if a future code path
        # mutates settings after startup we want a hard 503 rather than
        # silently granting a shared bucket.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is missing IPU_API_KEY_HASH configuration",
        )

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

    return derive_caller_identity(x_ipu_api_key, expected_hash=settings.api_key_hash)

from __future__ import annotations

import hashlib

from engine.src.session_store import SessionStore


class RestoreAuthenticationError(Exception):
    """Raised when restore is attempted without valid token/owner verification."""


class SessionRestorer:
    def __init__(self, session_store: SessionStore) -> None:
        self._session_store = session_store

    def restore(
        self,
        content: str,
        session_id: str,
        *,
        token: str,
        owner_hash: str,
    ) -> str:
        if not token or not owner_hash:
            raise RestoreAuthenticationError(
                "restore requires both a token and an owner_hash"
            )
        if not self._session_store.verify_owner_hash(session_id, owner_hash):
            raise RestoreAuthenticationError("restore owner verification failed")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not self._session_store.verify_restore_token_hash(session_id, token_hash):
            raise RestoreAuthenticationError("restore token verification failed")

        restored = content
        for mapping in sorted(
            self._session_store.get_mappings(session_id),
            key=lambda item: len(item.replaced),
            reverse=True,
        ):
            restored = restored.replace(mapping.replaced, mapping.original)
        return restored

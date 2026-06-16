from __future__ import annotations

from engine.src.session_store import (
    SessionStore,
    SQLiteSessionStore,
)

from app.core.settings import get_settings


class SessionHistoryUnavailableError(Exception):
    """세션 히스토리 기능은 SQLite 모드에서만 지원됩니다."""
    pass


class SessionOwnershipError(Exception):
    """Raised when a caller requests a session they do not own."""


class SessionService:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._store: SessionStore = self._build_session_store()

    def _build_session_store(self) -> SessionStore:
        if self._settings.session_store_kind == "memory":
            raise SessionHistoryUnavailableError(
                "세션 히스토리 API는 SQLite 모드에서만 지원됩니다. "
                "IPU_SESSION_STORE_KIND=sqlite로 설정해 주세요."
            )
        return SQLiteSessionStore(
            db_path=self._settings.session_store_path,
            ttl_seconds=self._settings.session_ttl_seconds,
        )

    def list_sessions(self, limit: int = 50, owner_hash: str = "dev-local") -> list[dict]:
        # Filter at the service layer: only return sessions owned by the caller.
        # ``owner_hash`` is supplied by the auth dependency; in dev mode it is
        # always ``"dev-local"``.
        all_sessions = self._store.list_sessions(limit=limit)
        return [
            s
            for s in all_sessions
            if self._store.verify_owner_hash(s["session_id"], owner_hash)
        ]

    def get_session_metadata(
        self, session_id: str, owner_hash: str = "dev-local"
    ) -> dict | None:
        if not self._store.verify_owner_hash(session_id, owner_hash):
            return None
        return self._store.get_session_metadata(session_id)

    def get_mappings(self, session_id: str, owner_hash: str = "dev-local") -> list:
        if not self._store.verify_owner_hash(session_id, owner_hash):
            raise SessionOwnershipError(session_id)
        return self._store.get_mappings(session_id)

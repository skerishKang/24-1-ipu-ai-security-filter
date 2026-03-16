from __future__ import annotations

from engine.src.session_store import (
    SessionStore,
    SQLiteSessionStore,
)

from app.core.settings import get_settings


class SessionHistoryUnavailableError(Exception):
    """세션 히스토리 기능은 SQLite 모드에서만 지원됩니다."""
    pass


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

    def list_sessions(self, limit: int = 50) -> list[dict]:
        return self._store.list_sessions(limit=limit)

    def get_session_metadata(self, session_id: str) -> dict | None:
        return self._store.get_session_metadata(session_id)

    def get_mappings(self, session_id: str) -> list:
        return self._store.get_mappings(session_id)

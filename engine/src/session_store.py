from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Callable

from engine.src.contracts import SessionMapping

DEFAULT_SESSION_TTL_SECONDS = 900


@dataclass
class SessionRecord:
    mappings: list[SessionMapping]
    expires_at: float


class InMemorySessionStore:
    def __init__(
        self,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._clock = clock or time
        self._store: dict[str, SessionRecord] = {}

    def save_mapping(self, session_id: str, mapping: SessionMapping) -> None:
        self.cleanup_expired_sessions()
        record = self._store.get(session_id)
        if record is None or self.is_expired(session_id):
            record = SessionRecord(mappings=[], expires_at=self._build_expiration())
            self._store[session_id] = record

        record.mappings.append(mapping)
        record.expires_at = self._build_expiration()

    def get_mappings(self, session_id: str) -> list[SessionMapping]:
        if self.is_expired(session_id):
            self.clear(session_id)
            return []

        record = self._store.get(session_id)
        if record is None:
            return []
        return list(record.mappings)

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def cleanup_expired_sessions(self) -> None:
        expired_ids = [
            session_id
            for session_id, record in self._store.items()
            if record.expires_at <= self._clock()
        ]
        for session_id in expired_ids:
            self.clear(session_id)

    def is_expired(self, session_id: str) -> bool:
        record = self._store.get(session_id)
        if record is None:
            return False
        return record.expires_at <= self._clock()

    def _build_expiration(self) -> float:
        return self._clock() + self.ttl_seconds

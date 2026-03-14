from __future__ import annotations

from engine.src.session_store import InMemorySessionStore


class SessionRestorer:
    def __init__(self, session_store: InMemorySessionStore) -> None:
        self._session_store = session_store

    def restore(self, content: str, session_id: str) -> str:
        restored = content
        for mapping in self._session_store.get_mappings(session_id):
            restored = restored.replace(mapping.replaced, mapping.original)
        return restored

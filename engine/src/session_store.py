from __future__ import annotations

import hmac
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import time
from typing import Callable, Protocol

from engine.src.contracts import SessionMapping

DEFAULT_SESSION_TTL_SECONDS = 900
SQLITE_SESSION_DIR_MODE = 0o700
SQLITE_SESSION_FILE_MODE = 0o600


@dataclass
class SessionRecord:
    mappings: list[SessionMapping]
    expires_at: float
    restore_token_hash: str | None = None
    owner_hash: str | None = None


class SessionStore(Protocol):
    ttl_seconds: int

    def save_mapping(self, session_id: str, mapping: SessionMapping) -> None: ...
    def save_restore_token_hash(self, session_id: str, token_hash: str) -> None: ...
    def save_owner_hash(self, session_id: str, owner_hash: str) -> None: ...
    def verify_restore_token_hash(self, session_id: str, token_hash: str) -> bool: ...
    def verify_owner_hash(self, session_id: str, owner_hash: str) -> bool: ...
    def get_mappings(self, session_id: str) -> list[SessionMapping]: ...
    def clear(self, session_id: str) -> None: ...
    def cleanup_expired_sessions(self) -> None: ...


class InMemorySessionStore:
    def __init__(
        self,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._clock = clock or time
        self._store: dict[str, SessionRecord] = {}
        self._lock = RLock()

    def save_mapping(self, session_id: str, mapping: SessionMapping) -> None:
        with self._lock:
            self._cleanup_expired_sessions_locked()
            record = self._get_or_create_record_locked(session_id)
            record.mappings.append(mapping)
            record.expires_at = self._build_expiration()

    def save_restore_token_hash(self, session_id: str, token_hash: str) -> None:
        with self._lock:
            self._cleanup_expired_sessions_locked()
            record = self._get_or_create_record_locked(session_id)
            record.restore_token_hash = token_hash
            record.expires_at = self._build_expiration()

    def save_owner_hash(self, session_id: str, owner_hash: str) -> None:
        with self._lock:
            self._cleanup_expired_sessions_locked()
            record = self._get_or_create_record_locked(session_id)
            record.owner_hash = owner_hash
            record.expires_at = self._build_expiration()

    def verify_restore_token_hash(self, session_id: str, token_hash: str) -> bool:
        with self._lock:
            if self._is_expired_locked(session_id):
                self.clear(session_id)
                return False
            record = self._store.get(session_id)
            if record is None or record.restore_token_hash is None:
                return False
            return hmac.compare_digest(record.restore_token_hash, token_hash)

    def verify_owner_hash(self, session_id: str, owner_hash: str) -> bool:
        with self._lock:
            if self._is_expired_locked(session_id):
                self.clear(session_id)
                return False
            record = self._store.get(session_id)
            if record is None or record.owner_hash is None:
                return False
            return hmac.compare_digest(record.owner_hash, owner_hash)

    def get_mappings(self, session_id: str) -> list[SessionMapping]:
        with self._lock:
            if self._is_expired_locked(session_id):
                self.clear(session_id)
                return []

            record = self._store.get(session_id)
            if record is None:
                return []
            return list(record.mappings)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def cleanup_expired_sessions(self) -> None:
        with self._lock:
            self._cleanup_expired_sessions_locked()

    def _get_or_create_record_locked(self, session_id: str) -> SessionRecord:
        record = self._store.get(session_id)
        if record is None or self._is_expired_locked(session_id):
            record = SessionRecord(mappings=[], expires_at=self._build_expiration())
            self._store[session_id] = record
        return record

    def _cleanup_expired_sessions_locked(self) -> None:
        expired_ids = [
            session_id
            for session_id, record in self._store.items()
            if record.expires_at <= self._clock()
        ]
        for session_id in expired_ids:
            self._store.pop(session_id, None)

    def is_expired(self, session_id: str) -> bool:
        with self._lock:
            return self._is_expired_locked(session_id)

    def _is_expired_locked(self, session_id: str) -> bool:
        record = self._store.get(session_id)
        if record is None:
            return False
        return record.expires_at <= self._clock()

    def _build_expiration(self) -> float:
        return self._clock() + self.ttl_seconds


class SQLiteSessionStore:
    def __init__(
        self,
        db_path: str | Path,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._clock = clock or time
        self._db_path = Path(db_path)
        self._prepare_storage_path()
        self._lock = RLock()
        self._initialize()
        self._apply_file_permissions()

    def save_mapping(self, session_id: str, mapping: SessionMapping) -> None:
        expires_at = self._build_expiration()
        with self._lock, self._connect() as conn:
            self._cleanup_expired_sessions_locked(conn)
            conn.execute(
                """
                INSERT INTO session_mappings (
                    session_id, original, replaced, type, expires_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, mapping.original, mapping.replaced, mapping.type, expires_at),
            )
            self._upsert_session_expiration(conn, session_id, expires_at)
            conn.commit()
            self._apply_file_permissions()

    def save_restore_token_hash(self, session_id: str, token_hash: str) -> None:
        expires_at = self._build_expiration()
        with self._lock, self._connect() as conn:
            self._cleanup_expired_sessions_locked(conn)
            conn.execute(
                """
                INSERT INTO session_restore_tokens (session_id, token_hash, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id)
                DO UPDATE SET token_hash=excluded.token_hash, expires_at=excluded.expires_at
                """,
                (session_id, token_hash, expires_at),
            )
            self._upsert_session_expiration(conn, session_id, expires_at)
            conn.commit()
            self._apply_file_permissions()

    def save_owner_hash(self, session_id: str, owner_hash: str) -> None:
        expires_at = self._build_expiration()
        with self._lock, self._connect() as conn:
            self._cleanup_expired_sessions_locked(conn)
            conn.execute(
                """
                INSERT INTO session_owners (session_id, owner_hash, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id)
                DO UPDATE SET owner_hash=excluded.owner_hash, expires_at=excluded.expires_at
                """,
                (session_id, owner_hash, expires_at),
            )
            self._upsert_session_expiration(conn, session_id, expires_at)
            conn.commit()
            self._apply_file_permissions()

    def verify_restore_token_hash(self, session_id: str, token_hash: str) -> bool:
        with self._lock, self._connect() as conn:
            if self._is_expired_locked(conn, session_id):
                self.clear(session_id)
                return False
            now = self._clock()
            row = conn.execute(
                """
                SELECT token_hash FROM session_restore_tokens
                WHERE session_id = ? AND expires_at > ?
                """,
                (session_id, now),
            ).fetchone()
            if row is None:
                return False
            return hmac.compare_digest(str(row["token_hash"]), token_hash)

    def verify_owner_hash(self, session_id: str, owner_hash: str) -> bool:
        with self._lock, self._connect() as conn:
            if self._is_expired_locked(conn, session_id):
                self.clear(session_id)
                return False
            now = self._clock()
            row = conn.execute(
                """
                SELECT owner_hash FROM session_owners
                WHERE session_id = ? AND expires_at > ?
                """,
                (session_id, now),
            ).fetchone()
            if row is None:
                return False
            return hmac.compare_digest(str(row["owner_hash"]), owner_hash)

    def list_sessions(self, limit: int = 50) -> list[dict]:
        with self._lock, self._connect() as conn:
            self._cleanup_expired_sessions_locked(conn)
            now = self._clock()
            rows = conn.execute(
                """
                SELECT session_id, MAX(expires_at) as expires_at
                FROM session_mappings
                WHERE expires_at > ?
                GROUP BY session_id
                ORDER BY expires_at DESC
                LIMIT ?
                """,
                (now, limit),
            ).fetchall()
            return [
                {"session_id": row["session_id"], "expires_at": row["expires_at"]}
                for row in rows
            ]

    def get_session_metadata(self, session_id: str) -> dict | None:
        with self._lock, self._connect() as conn:
            if self._is_expired_locked(conn, session_id):
                self.clear(session_id)
                return None
            now = self._clock()
            row = conn.execute(
                """
                SELECT session_id, expires_at, COUNT(*) as mapping_count
                FROM session_mappings
                WHERE session_id = ? AND expires_at > ?
                """,
                (session_id, now),
            ).fetchone()
            if row is None:
                return None
            return {
                "session_id": row["session_id"],
                "mapping_count": row["mapping_count"],
                "expires_at": row["expires_at"],
            }

    def get_mappings(self, session_id: str) -> list[SessionMapping]:
        with self._lock, self._connect() as conn:
            if self._is_expired_locked(conn, session_id):
                self.clear(session_id)
                return []

            rows = conn.execute(
                """
                SELECT session_id, original, replaced, type
                FROM session_mappings
                WHERE session_id = ?
                ORDER BY rowid ASC
                """,
                (session_id,),
            ).fetchall()
            return [
                SessionMapping(
                    session_id=row["session_id"],
                    original=row["original"],
                    replaced=row["replaced"],
                    type=row["type"],
                )
                for row in rows
            ]

    def clear(self, session_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM session_mappings WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM session_expirations WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM session_restore_tokens WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM session_owners WHERE session_id = ?", (session_id,))
            conn.commit()

    def cleanup_expired_sessions(self) -> None:
        with self._lock, self._connect() as conn:
            self._cleanup_expired_sessions_locked(conn)
            conn.commit()

    def _prepare_storage_path(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._chmod_if_supported(self._db_path.parent, SQLITE_SESSION_DIR_MODE)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_mappings (
                    session_id TEXT NOT NULL,
                    original TEXT NOT NULL,
                    replaced TEXT NOT NULL,
                    type TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_expirations (
                    session_id TEXT PRIMARY KEY,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_restore_tokens (
                    session_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_owners (
                    session_id TEXT PRIMARY KEY,
                    owner_hash TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_mappings_session_id ON session_mappings(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_mappings_expires_at ON session_mappings(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_expirations_expires_at ON session_expirations(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_restore_tokens_expires_at ON session_restore_tokens(expires_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_owners_expires_at ON session_owners(expires_at)"
            )
            conn.commit()

    def _upsert_session_expiration(self, conn: sqlite3.Connection, session_id: str, expires_at: float) -> None:
        conn.execute(
            """
            INSERT INTO session_expirations (session_id, expires_at)
            VALUES (?, ?)
            ON CONFLICT(session_id) DO UPDATE SET expires_at=excluded.expires_at
            """,
            (session_id, expires_at),
        )

    def _apply_file_permissions(self) -> None:
        self._chmod_if_supported(self._db_path, SQLITE_SESSION_FILE_MODE)

    def _chmod_if_supported(self, path: Path, mode: int) -> None:
        if os.name == "nt" or not path.exists():
            return
        try:
            path.chmod(mode)
        except OSError:
            return

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _cleanup_expired_sessions_locked(self, conn: sqlite3.Connection) -> None:
        now = self._clock()
        expired_ids = [
            row["session_id"]
            for row in conn.execute(
                "SELECT session_id FROM session_expirations WHERE expires_at <= ?",
                (now,),
            ).fetchall()
        ]
        if not expired_ids:
            conn.execute("DELETE FROM session_restore_tokens WHERE expires_at <= ?", (now,))
            conn.execute("DELETE FROM session_owners WHERE expires_at <= ?", (now,))
            return

        conn.executemany(
            "DELETE FROM session_mappings WHERE session_id = ?",
            [(session_id,) for session_id in expired_ids],
        )
        conn.executemany(
            "DELETE FROM session_expirations WHERE session_id = ?",
            [(session_id,) for session_id in expired_ids],
        )
        conn.executemany(
            "DELETE FROM session_restore_tokens WHERE session_id = ?",
            [(session_id,) for session_id in expired_ids],
        )
        conn.executemany(
            "DELETE FROM session_owners WHERE session_id = ?",
            [(session_id,) for session_id in expired_ids],
        )
        conn.execute("DELETE FROM session_restore_tokens WHERE expires_at <= ?", (now,))
        conn.execute("DELETE FROM session_owners WHERE expires_at <= ?", (now,))

    def _is_expired_locked(self, conn: sqlite3.Connection, session_id: str) -> bool:
        row = conn.execute(
            "SELECT expires_at FROM session_expirations WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return False
        return float(row["expires_at"]) <= self._clock()

    def _build_expiration(self) -> float:
        return self._clock() + self.ttl_seconds

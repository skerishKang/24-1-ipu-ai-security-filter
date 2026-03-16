#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.settings import get_settings
from engine.src.session_store import SQLiteSessionStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or clean up the manual-preview SQLite session store."
    )
    parser.add_argument(
        "command",
        choices=("stats", "cleanup"),
        help="Show current store stats or remove expired sessions.",
    )
    parser.add_argument(
        "--db-path",
        help="Override the SQLite session store path. Defaults to IPU_SESSION_STORE_PATH or project default.",
    )
    return parser


def resolve_db_path(explicit_db_path: str | None) -> Path:
    if explicit_db_path:
        return Path(explicit_db_path).expanduser()
    return get_settings().session_store_path


def collect_stats(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {
            "session_count": 0,
            "mapping_count": 0,
            "expired_session_count": 0,
        }

    with sqlite3.connect(db_path) as conn:
        session_count = conn.execute("SELECT COUNT(*) FROM session_expirations").fetchone()[0]
        mapping_count = conn.execute("SELECT COUNT(*) FROM session_mappings").fetchone()[0]
        expired_session_count = conn.execute(
            "SELECT COUNT(*) FROM session_expirations WHERE expires_at <= strftime('%s','now')"
        ).fetchone()[0]

    return {
        "session_count": int(session_count),
        "mapping_count": int(mapping_count),
        "expired_session_count": int(expired_session_count),
    }


def print_stats(db_path: Path) -> None:
    stats = collect_stats(db_path)
    print("IPU manual-preview session store")
    print(f"- db_path: {db_path}")
    print(f"- session_count: {stats['session_count']}")
    print(f"- mapping_count: {stats['mapping_count']}")
    print(f"- expired_session_count: {stats['expired_session_count']}")


def cleanup_expired(db_path: Path) -> None:
    store = SQLiteSessionStore(db_path=db_path)
    before = collect_stats(db_path)
    store.cleanup_expired_sessions()
    after = collect_stats(db_path)

    print("IPU manual-preview session cleanup")
    print(f"- db_path: {db_path}")
    print(f"- sessions_before: {before['session_count']}")
    print(f"- sessions_after: {after['session_count']}")
    print(f"- expired_sessions_before: {before['expired_session_count']}")
    print(f"- mappings_before: {before['mapping_count']}")
    print(f"- mappings_after: {after['mapping_count']}")


def main() -> int:
    args = build_parser().parse_args()
    db_path = resolve_db_path(args.db_path)

    if args.command == "stats":
        print_stats(db_path)
        return 0

    cleanup_expired(db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

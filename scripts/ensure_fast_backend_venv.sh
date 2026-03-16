#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
TARGET_VENV="${IPU_FAST_BACKEND_VENV:-/tmp/ipu_backend_test_venv}"
MARKER_FILE="$TARGET_VENV/.ipu_backend_requirements.sha256"
REQ_HASH="$(sha256sum "$BACKEND_DIR/requirements.txt" "$ROOT/pyproject.toml" | sha256sum | cut -d' ' -f1)"

if [[ ! -x "$TARGET_VENV/bin/python" ]]; then
  echo "[IPU] Creating fast backend venv at $TARGET_VENV" >&2
  python3 -m venv "$TARGET_VENV"
fi

INSTALLED_HASH=""
if [[ -f "$MARKER_FILE" ]]; then
  INSTALLED_HASH="$(cat "$MARKER_FILE")"
fi

if [[ "$INSTALLED_HASH" != "$REQ_HASH" ]]; then
  echo "[IPU] Installing backend dependencies into $TARGET_VENV" >&2
  (
    cd "$BACKEND_DIR"
    "$TARGET_VENV/bin/pip" install -r requirements.txt
  )
  printf '%s\n' "$REQ_HASH" > "$MARKER_FILE"
fi

printf '%s\n' "$TARGET_VENV/bin/python"

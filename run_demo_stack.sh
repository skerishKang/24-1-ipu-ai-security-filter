#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
BACKEND_URL="http://127.0.0.1:8241/health"
FRONTEND_URL="http://127.0.0.1:4241"

echo "[IPU] Checking demo-stack dependencies..."
python3 "$ROOT/scripts/check_demo_stack_deps.py"
echo

if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv/bin/python"
elif [[ -x "$BACKEND_DIR/.venv-win/Scripts/python.exe" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv-win/Scripts/python.exe"
else
  BACKEND_PY="python3"
fi

check_url() {
  local url="$1"
  python3 - "$url" <<'PY'
import sys
import urllib.request

url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=2) as response:
        sys.exit(0 if response.status >= 200 else 1)
except Exception:
    sys.exit(1)
PY
}

if ! check_url "$BACKEND_URL"; then
  echo "[IPU] Starting backend on 8241..."
  (
    cd "$BACKEND_DIR"
    nohup "$BACKEND_PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8241 > "$ROOT/backend.log" 2>&1 &
  )
else
  echo "[IPU] Backend already responding on 8241. Skipping."
fi

if ! check_url "$FRONTEND_URL"; then
  echo "[IPU] Starting frontend on 4241..."
  (
    cd "$FRONTEND_DIR"
    nohup python3 -m http.server 4241 > "$ROOT/frontend.log" 2>&1 &
  )
else
  echo "[IPU] Frontend already responding on 4241. Skipping."
fi

echo
echo "[IPU] Stack launch requested."
echo "Backend:  $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo
echo "Use ./run_verification_suite.sh after both services are up."

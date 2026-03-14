#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"

if [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv/bin/python"
elif [[ -x "$BACKEND_DIR/.venv-win/Scripts/python.exe" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv-win/Scripts/python.exe"
else
  BACKEND_PY="python3"
fi

echo "[1/5] Engine unit + quality tests"
cd "$ROOT"
echo "Using backend port 8241 and frontend port 4241 for live checks."
python3 -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness
python3 engine/scripts/run_quality_harness.py

echo
echo "[2/5] Backend API smoke tests"
cd "$BACKEND_DIR"
"$BACKEND_PY" -m unittest tests.test_manual_preview_api

echo
echo "[3/5] Frontend browser smoke tests"
cd "$FRONTEND_DIR"
node tests/runSmokeTests.js

echo
echo "[4/5] Frontend-backend live integration tests"
node tests/runLiveIntegrationTests.js

echo
echo "[5/5] Verification suite completed successfully."

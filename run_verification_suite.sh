#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
FAST_BACKEND_VENV_SCRIPT="$ROOT/scripts/ensure_fast_backend_venv.sh"

if [[ -x "$BACKEND_DIR/.venv-win/Scripts/python.exe" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv-win/Scripts/python.exe"
elif [[ -x "$FAST_BACKEND_VENV_SCRIPT" ]]; then
  BACKEND_PY="$("$FAST_BACKEND_VENV_SCRIPT")"
elif [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  BACKEND_PY="$BACKEND_DIR/.venv/bin/python"
else
  BACKEND_PY="python3"
fi

echo "[1/5] Engine unit + quality tests"
cd "$ROOT"
echo "Using backend port 8241 and frontend port 4241 for live checks."
python3 -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness
python3 engine/scripts/run_quality_harness.py

echo
echo "[2/5] Backend API + guardrail + PDF quality tests"
cd "$BACKEND_DIR"
echo "Using backend python: $BACKEND_PY"
"$BACKEND_PY" -m unittest \
  tests.test_manual_preview_api \
  tests.test_manual_preview_restore_limits \
  tests.test_upload_guardrails \
  tests.test_file_parser \
  tests.test_pdf_quality_samples

echo
echo "[3/5] Frontend unit + browser smoke tests"
cd "$FRONTEND_DIR"
node tests/resultRendering.test.js
node tests/runSmokeTests.js

echo
echo "[4/5] Frontend-backend live integration tests"
node tests/runLiveIntegrationTests.js

if [[ "${IPU_RUN_AUDIO_LIVE_SMOKE:-0}" == "1" ]]; then
  echo
  echo "[opt-in] Real audio API smoke"
  cd "$ROOT"
  python3 scripts/run_real_whisper_api_smoke.py
fi

if [[ "${IPU_RUN_LONG_AUDIO_BENCHMARK:-0}" == "1" ]]; then
  echo
  echo "[opt-in] Long audio benchmark"
  cd "$ROOT"
  python3 scripts/run_whisper_duration_benchmark.py
fi

echo
echo "[5/5] Verification suite completed successfully."

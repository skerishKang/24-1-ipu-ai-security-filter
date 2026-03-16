@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "BACKEND_URL=http://127.0.0.1:8241/health"
set "FRONTEND_URL=http://127.0.0.1:4241"

echo [IPU] Checking demo-stack dependencies...
python "%ROOT%scripts\check_demo_stack_deps.py"
echo.

set "BACKEND_PY="
if exist "%BACKEND_DIR%\.venv-win\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv-win\Scripts\python.exe"
if not defined BACKEND_PY if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv\Scripts\python.exe"
if not defined BACKEND_PY set "BACKEND_PY=python"

call :check_url "%BACKEND_URL%"
if errorlevel 1 (
  echo [IPU] Starting backend in a new window...
  start "IPU Backend" cmd /k "cd /d "%BACKEND_DIR%" && "%BACKEND_PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8241"
) else (
  echo [IPU] Backend already responding on 8241. Skipping new backend window.
)

call :check_url "%FRONTEND_URL%"
if errorlevel 1 (
  echo [IPU] Starting frontend in a new window...
  start "IPU Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && python -m http.server 4241"
) else (
  echo [IPU] Frontend already responding on 4241. Skipping new frontend window.
)

echo.
echo [IPU] Stack launch requested.
echo Backend:  http://127.0.0.1:8241/health
echo Frontend: http://127.0.0.1:4241
echo.
echo Use run_verification_suite.bat after both windows are up.
endlocal
goto :eof

:check_url
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%~1' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%

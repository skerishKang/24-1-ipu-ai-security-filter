@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_URL=http://127.0.0.1:8241/health"
set "FRONTEND_URL=http://127.0.0.1:4241"

echo [IPU] Checking if services are already running...
echo.

call :check_url "Backend" "%BACKEND_URL%"
if errorlevel 1 (
    echo [IPU] Starting backend...
    start "IPU Backend" cmd /k ""%ROOT%open-backend.bat""
) else (
    echo [IPU] Backend already running on 8241.
)

call :check_url "Frontend" "%FRONTEND_URL%"
if errorlevel 1 (
    echo [IPU] Starting frontend...
    start "IPU Frontend" cmd /k ""%ROOT%open-frontend.bat""
) else (
    echo [IPU] Frontend already running on 4241.
)

echo.
echo [IPU] Done.
echo Backend:  http://127.0.0.1:8241/health
echo Frontend: http://127.0.0.1:4241
echo.
pause
exit /b 0

:check_url
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri '%~2' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -ge 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
exit /b %errorlevel%

@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

cd /d "%FRONTEND_DIR%"
echo [IPU Frontend] Starting HTTP server...
echo [IPU Frontend] Dir: %CD%
echo [IPU Frontend] URL: http://127.0.0.1:4241
echo.
python -m http.server 4241
if errorlevel 1 (
    echo.
    echo [IPU Frontend] ERROR: Failed to start. Press any key to close...
    pause >nul
)

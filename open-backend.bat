@echo off

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

if exist "%BACKEND_DIR%\.venv-win\Scripts\python.exe" (
    set "PYTHON=%BACKEND_DIR%\.venv-win\Scripts\python.exe"
) else if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

cd /d "%BACKEND_DIR%"
echo [IPU Backend] Starting uvicorn...
echo [IPU Backend] Using: %PYTHON%
echo [IPU Backend] Dir: %CD%
echo [IPU Backend] Project: %PROJECT_ROOT%
echo [IPU Backend] URL: http://127.0.0.1:8241/health
echo.

set PYTHONPATH=%PROJECT_ROOT%
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8241
if errorlevel 1 (
    echo.
    echo [IPU Backend] ERROR: Failed to start.
    echo Check if dependencies are installed:
    echo   pip install -r requirements.txt
    echo.
    pause
)

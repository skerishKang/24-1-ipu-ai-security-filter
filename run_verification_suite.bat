@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

set "BACKEND_PY="
if exist "%BACKEND_DIR%\.venv-win\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv-win\Scripts\python.exe"
if not defined BACKEND_PY if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv\Scripts\python.exe"
if not defined BACKEND_PY set "BACKEND_PY=python"

echo [1/5] Engine unit + quality tests
cd /d "%ROOT%"
echo Using backend port 8241 and frontend port 4241 for live checks.
python -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness || goto :fail
python engine\scripts\run_quality_harness.py || goto :fail

echo.
echo [2/5] Backend API smoke tests
cd /d "%BACKEND_DIR%"
"%BACKEND_PY%" -m unittest tests.test_manual_preview_api || goto :fail

echo.
echo [3/5] Frontend browser smoke tests
cd /d "%FRONTEND_DIR%"
node tests\runSmokeTests.js || goto :fail

echo.
echo [4/5] Frontend-backend live integration tests
node tests\runLiveIntegrationTests.js || goto :fail

echo.
echo [5/5] Verification suite completed successfully.
pause
goto :eof

:fail
echo.
echo Verification suite failed.
pause
exit /b 1

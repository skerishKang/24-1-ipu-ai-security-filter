@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

set "BACKEND_PY="
if exist "%BACKEND_DIR%\.venv-win\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv-win\Scripts\python.exe"
if not defined BACKEND_PY if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" set "BACKEND_PY=%BACKEND_DIR%\.venv\Scripts\python.exe"
if not defined BACKEND_PY set "BACKEND_PY=python"

set "BACKEND_PID="
set "FRONTEND_PID="
set "RUN_ID=%RANDOM%-%RANDOM%"
set "BACKEND_PID_FILE=%TEMP%\ipu-backend-%RUN_ID%.pid"
set "FRONTEND_PID_FILE=%TEMP%\ipu-frontend-%RUN_ID%.pid"
set "BACKEND_STDOUT=%TEMP%\ipu-backend-%RUN_ID%.out.log"
set "BACKEND_STDERR=%TEMP%\ipu-backend-%RUN_ID%.err.log"
set "FRONTEND_STDOUT=%TEMP%\ipu-frontend-%RUN_ID%.out.log"
set "FRONTEND_STDERR=%TEMP%\ipu-frontend-%RUN_ID%.err.log"


echo [1/5] Engine unit + quality tests
cd /d "%ROOT%"
echo Using backend port 8241 and frontend port 4241 for live checks.
python -m unittest engine.tests.test_manual_preview_engine engine.tests.test_quality_harness || goto :fail
python engine\scripts\run_quality_harness.py || goto :fail


echo.
echo [2/5] Backend API + guardrail + PDF quality tests
cd /d "%BACKEND_DIR%"
"%BACKEND_PY%" -m unittest tests.test_manual_preview_api tests.test_manual_preview_local_rewrite_api tests.test_manual_preview_restore_limits tests.test_manual_preview_response_mode tests.test_upload_guardrails tests.test_upload_concurrent_requests tests.test_upload_streaming_read_guard tests.test_file_parser tests.test_audio_duration_prober tests.test_parser_limit_coverage tests.test_pdf_quality_samples || goto :fail


echo.
echo [3/5] Frontend unit + browser smoke tests
cd /d "%FRONTEND_DIR%"
node tests\resultRendering.test.js || goto :fail
node tests\runSmokeTests.js || goto :fail


echo.
echo [4/5] Frontend-backend live integration tests
call :assert_live_ports_free
if errorlevel 1 goto :fail

call :start_live_servers
if errorlevel 1 goto :fail

call :wait_for_live_servers
if errorlevel 1 goto :fail

cd /d "%FRONTEND_DIR%"
node tests\runLiveIntegrationTests.js || goto :fail
echo [live] Live integration completed successfully.
call :stop_live_servers
if errorlevel 1 goto :fail

if "%IPU_RUN_AUDIO_LIVE_SMOKE%"=="1" (
  echo.
  echo [opt-in] Real audio API smoke
  cd /d "%ROOT%"
  python scripts\run_real_whisper_api_smoke.py || goto :fail
)

if "%IPU_RUN_LONG_AUDIO_BENCHMARK%"=="1" (
  echo.
  echo [opt-in] Long audio benchmark
  cd /d "%ROOT%"
  python scripts\run_whisper_duration_benchmark.py || goto :fail
)


echo.
echo [5/5] Verification suite completed successfully.
call :remove_live_logs
if not "%IPU_NO_PAUSE%"=="1" pause
exit /b 0


:assert_live_ports_free
echo [live] Checking that ports 8241 and 4241 are available...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$occupied = @(); foreach ($port in @(8241, 4241)) { $client = New-Object System.Net.Sockets.TcpClient; try { $client.Connect('127.0.0.1', $port); $occupied += $port } catch { } finally { $client.Dispose() } }; if ($occupied.Count -gt 0) { Write-Host ('Ports already in use: ' + ($occupied -join ', ')); exit 1 }; exit 0"
if errorlevel 1 (
  echo [live] Refusing to use or terminate processes that were not started by this run.
  exit /b 1
)
echo [live] Ports are available.
exit /b 0


:start_live_servers
echo [live] Starting backend with: "%BACKEND_PY%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $process = $null; try { $backendDir = '"' + $env:BACKEND_DIR + '"'; $arguments = @('-m','uvicorn','app.main:app','--app-dir',$backendDir,'--host','127.0.0.1','--port','8241'); $process = Start-Process -FilePath $env:BACKEND_PY -ArgumentList $arguments -WorkingDirectory $env:ROOT -RedirectStandardOutput $env:BACKEND_STDOUT -RedirectStandardError $env:BACKEND_STDERR -PassThru; Set-Content -LiteralPath $env:BACKEND_PID_FILE -Value $process.Id -Encoding ascii } catch { if ($process) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue }; Write-Error $_; exit 1 }"
if errorlevel 1 (
  echo [live] Failed to start backend process.
  exit /b 1
)
if not exist "%BACKEND_PID_FILE%" (
  echo [live] Backend PID file was not created.
  exit /b 1
)
set /p BACKEND_PID=<"%BACKEND_PID_FILE%"
if not defined BACKEND_PID (
  echo [live] Backend PID was not captured.
  exit /b 1
)
echo [live] Backend PID: %BACKEND_PID%

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $process = $null; try { $frontendDir = '"' + $env:FRONTEND_DIR + '"'; $arguments = @('-m','http.server','4241','--directory',$frontendDir,'--bind','127.0.0.1'); $process = Start-Process -FilePath $env:BACKEND_PY -ArgumentList $arguments -WorkingDirectory $env:ROOT -RedirectStandardOutput $env:FRONTEND_STDOUT -RedirectStandardError $env:FRONTEND_STDERR -PassThru; Set-Content -LiteralPath $env:FRONTEND_PID_FILE -Value $process.Id -Encoding ascii } catch { if ($process) { Stop-Process -Id $process.Id -ErrorAction SilentlyContinue }; Write-Error $_; exit 1 }"
if errorlevel 1 (
  echo [live] Failed to start frontend process.
  exit /b 1
)
if not exist "%FRONTEND_PID_FILE%" (
  echo [live] Frontend PID file was not created.
  exit /b 1
)
set /p FRONTEND_PID=<"%FRONTEND_PID_FILE%"
if not defined FRONTEND_PID (
  echo [live] Frontend PID was not captured.
  exit /b 1
)
echo [live] Frontend PID: %FRONTEND_PID%
exit /b 0


:wait_for_live_servers
echo [live] Waiting up to 30 seconds for backend and frontend readiness...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddSeconds(30); do { try { $backend = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8241/health' -TimeoutSec 2).StatusCode; $frontend = (Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:4241/' -TimeoutSec 2).StatusCode; if ($backend -eq 200 -and $frontend -eq 200) { exit 0 } } catch { }; Start-Sleep -Seconds 1 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
  echo [live] Readiness check failed.
  exit /b 1
)
echo [live] Backend and frontend are ready.
exit /b 0


:stop_live_servers
if not defined BACKEND_PID if not defined FRONTEND_PID exit /b 0

echo [live] Stopping processes started by this verification run...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$processIds = @(); if ($env:BACKEND_PID) { $processIds += [int]$env:BACKEND_PID }; if ($env:FRONTEND_PID) { $processIds += [int]$env:FRONTEND_PID }; $failed = @(); foreach ($processId in $processIds) { $process = Get-Process -Id $processId -ErrorAction SilentlyContinue; if ($process) { Stop-Process -Id $processId -ErrorAction SilentlyContinue; Wait-Process -Id $processId -Timeout 5 -ErrorAction SilentlyContinue }; if (Get-Process -Id $processId -ErrorAction SilentlyContinue) { $failed += $processId } }; if ($failed.Count -gt 0) { Write-Error ('Processes did not stop: ' + ($failed -join ', ')); exit 1 }; exit 0"
set "STOP_RESULT=%ERRORLEVEL%"
if not "%STOP_RESULT%"=="0" (
  echo [live] Cleanup failed for one or more captured PIDs.
  exit /b 1
)
if defined BACKEND_PID echo [live] Backend PID stopped: %BACKEND_PID%
if defined FRONTEND_PID echo [live] Frontend PID stopped: %FRONTEND_PID%
set "BACKEND_PID="
set "FRONTEND_PID="
call :remove_live_pid_files
echo [live] Cleanup completed.
exit /b 0


:show_live_logs
echo [live] Backend stdout: %BACKEND_STDOUT%
echo [live] Backend stderr: %BACKEND_STDERR%
echo [live] Frontend stdout: %FRONTEND_STDOUT%
echo [live] Frontend stderr: %FRONTEND_STDERR%
if exist "%BACKEND_STDERR%" (
  echo ----- backend stderr -----
  type "%BACKEND_STDERR%"
)
if exist "%FRONTEND_STDERR%" (
  echo ----- frontend stderr -----
  type "%FRONTEND_STDERR%"
)
exit /b 0


:remove_live_pid_files
if exist "%BACKEND_PID_FILE%" del /q "%BACKEND_PID_FILE%" >nul 2>&1
if exist "%FRONTEND_PID_FILE%" del /q "%FRONTEND_PID_FILE%" >nul 2>&1
exit /b 0


:remove_live_logs
if exist "%BACKEND_STDOUT%" del /q "%BACKEND_STDOUT%" >nul 2>&1
if exist "%BACKEND_STDERR%" del /q "%BACKEND_STDERR%" >nul 2>&1
if exist "%FRONTEND_STDOUT%" del /q "%FRONTEND_STDOUT%" >nul 2>&1
if exist "%FRONTEND_STDERR%" del /q "%FRONTEND_STDERR%" >nul 2>&1
exit /b 0


:fail
echo.
echo Verification suite failed.
call :stop_live_servers
call :remove_live_pid_files
call :show_live_logs
if not "%IPU_NO_PAUSE%"=="1" pause
exit /b 1

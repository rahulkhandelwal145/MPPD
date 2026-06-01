@echo off
setlocal

set FORCE=false
if /i "%1"=="--force" set FORCE=true

echo Running pipeline (force_refresh=%FORCE%)...

curl -s http://127.0.0.1:8000/api/v1/health >nul 2>&1
if errorlevel 1 (
    echo ERROR: Backend is not running. Start it first with start.bat
    exit /b 1
)

curl -s -X POST http://127.0.0.1:8000/api/v1/pipeline/run ^
     -H "Content-Type: application/json" ^
     -d "{\"force_refresh\": %FORCE%}"

echo.
echo Done. Check http://127.0.0.1:8000/api/v1/pipeline/run for status.
endlocal

@echo off
echo Stopping any existing backend/frontend processes...

REM Kill all python processes running uvicorn
tasklist /fi "imagename eq python.exe" /fo csv /nh 2>nul | findstr /i "python" >nul
if not errorlevel 1 (
    wmic process where "name='python.exe' and commandline like '%%uvicorn%%'" delete >nul 2>&1
)

REM Kill anything on port 5173 (Vite)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":5173" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo Starting MP Scorer...

start "Backend" cmd /k ".venv311\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload"

start "Frontend" cmd /k "cd frontend && npm run dev"

echo Backend: http://localhost:8000/api/v1/docs
echo Frontend: http://localhost:5173

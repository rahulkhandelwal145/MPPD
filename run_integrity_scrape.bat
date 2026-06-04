@echo off
setlocal

set FORCE=false
if /i "%1"=="--force" set FORCE=true

echo ============================================
echo  MyNeta Integrity Scraper (Phase 2)
echo  force_refresh=%FORCE%
echo ============================================
echo.

if "%FORCE%"=="true" (
    .venv311\Scripts\python.exe -c "import asyncio; from backend.agents.myneta_pipeline import run; asyncio.run(run(force_refresh=True))"
) else (
    .venv311\Scripts\python.exe -c "import asyncio; from backend.agents.myneta_pipeline import run; asyncio.run(run(force_refresh=False))"
)

echo.
echo Done. Check data\unmatched_candidates.log for name-matching issues.
endlocal

@echo off
setlocal

set LIMIT=
set SLUG=
set OFFSET=0

:parse
if /i "%1"=="--limit"  (set LIMIT=%2  & shift & shift & goto parse)
if /i "%1"=="--slug"   (set SLUG=%2   & shift & shift & goto parse)
if /i "%1"=="--offset" (set OFFSET=%2 & shift & shift & goto parse)

echo ============================================
echo  Public Statement Monitor Pipeline (Phase 4)
echo  Google News RSS ^> LLM quote extraction
echo  ^> classification ^> store non-E statements
if defined LIMIT echo  limit=%LIMIT%
if /i not "%OFFSET%"=="0" echo  offset=%OFFSET%
if defined SLUG  echo  slug=%SLUG%
echo ============================================
echo.
echo Note: full 543-MP run takes ~45h.
echo       Already-fetched articles are skipped on re-run.
echo       Groq rate limit falls back to local Ollama.
echo.

if not exist logs mkdir logs

if defined SLUG (
    .venv311\Scripts\python.exe -c "from backend.pipeline.news_pipeline import run_all_sync; r = run_all_sync(only_slug='%SLUG%'); print(r)"
) else if defined LIMIT (
    .venv311\Scripts\python.exe -c "from backend.pipeline.news_pipeline import run_all_sync; r = run_all_sync(limit=%LIMIT%, offset=%OFFSET%); print(r)"
) else (
    .venv311\Scripts\python.exe -c "from backend.pipeline.news_pipeline import run_all_sync; r = run_all_sync(offset=%OFFSET%); print(r)"
)

echo.
echo Done.
endlocal

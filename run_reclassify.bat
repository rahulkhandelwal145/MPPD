@echo off
setlocal

set LIMIT=
set SLUG=

:parse
if /i "%1"=="--limit" (set LIMIT=--limit %2 & shift & shift & goto parse)
if /i "%1"=="--slug"  (set SLUG=--slug %2  & shift & shift & goto parse)

echo ============================================
echo  Re-classify Stored Articles (Phase 4)
echo  Reads article text already in DB.
echo  No HTTP calls to news sites.
echo  Uses llama-3.3-70b for classification.
if defined LIMIT echo  %LIMIT%
if defined SLUG  echo  %SLUG%
echo ============================================
echo.

if not exist logs mkdir logs
.venv311\Scripts\python.exe -m backend.pipeline.reclassify_stored %SLUG% %LIMIT%

echo.
echo Done.
endlocal

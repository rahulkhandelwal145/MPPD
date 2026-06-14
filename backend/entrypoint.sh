#!/bin/sh
set -e

echo "Running Alembic migrations..."
# Must run from backend/ because alembic.ini uses a relative script_location
# PYTHONPATH=/app lets the migration scripts import from the backend package
( cd /app/backend && PYTHONPATH=/app python -m alembic upgrade 0005 )

echo "Starting uvicorn..."
# Single worker — APScheduler must not run in multiple processes
exec python -m uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1

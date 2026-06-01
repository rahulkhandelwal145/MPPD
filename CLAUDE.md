# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Python Environment

**Use `.venv311`** — Python 3.11 is required. `.venv` (Python 3.13) is missing `bs4`, `pandas`, and other scraper/scoring dependencies. All `python` and `pip` commands must use `.venv311\Scripts\python.exe`.

## Commands

```bash
# Backend (from project root)
.venv311\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (from project root)
cd frontend && npm run dev       # dev server on port 5173
cd frontend && npm run build

# Database migrations (must run from backend/ directory, not project root)
cd backend && python -m alembic upgrade head
cd backend && python -m alembic revision --autogenerate -m "description"

# Quick smoke tests
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/mps?limit=2"

# Trigger pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/run -H "Content-Type: application/json" -d '{"force_refresh": false}'
```

## Architecture

### Data Pipeline (the core of the app)

`POST /pipeline/run` fires an async background job. The orchestrator in `backend/agents/orchestrator.py` runs four agents in sequence, passing a shared `state` dict between them:

1. **prs_scraper_agent** — Fetches each MP's page from `prsindia.org/mptrack/18th-lok-sabha/{slug}`. Caches raw HTML in `data/cache/{slug}.html`. Parsing uses BeautifulSoup CSS selectors on structured divs (`.attendance`, `.debate`, `.questions`, `.pmb`) — each metric block has exactly three `div.field-item.even` in order: Selected MP value → National Average → State Average.

2. **mplads_agent** — Fetches MPLADS constituency fund utilization from data.gov.in API (requires `DATAGOV_API_KEY`). Matches MP names via fuzzy string matching (rapidfuzz). Gracefully skips if key is absent.

3. **scoring_agent** — Uses pandas to compute 0–10 percentile scores within two peer groups: `"minister"` and `"non-minister"`. Ministers are excluded from questions/debates/PMB ranking (those metrics are NULL for them). Only attendance is scored across all MPs.

4. **store_agent** — Upserts `mp_profiles` on `prs_slug` uniqueness, then inserts new rows into `mp_raw_data` and `mp_scores` (append-only; latest scores are found via `MAX(scored_at)` subquery).

### Database

MySQL only (driver: `asyncmy`). Four tables:
- `mp_profiles` — one row per MP, identity and biographical fields including `education`, `age`, `gender`
- `mp_raw_data` — append-only scrape results per pipeline run; includes national/state averages per metric
- `mp_scores` — append-only peer-normalized scores per pipeline run
- `pipeline_runs` — job tracking

Migration files live in `backend/db/migrations/versions/`. Alembic config is `backend/alembic.ini`; the `script_location` is relative so alembic must be invoked from `backend/`.

### API Routes

All routes under `/api/v1`. **Route ordering in `mps.py` is critical**: `/leaderboard` and `/stats/summary` must be declared before `/{slug}` or FastAPI will match them as slug values.

Scores are joined via a `MAX(scored_at)` subquery so the API always returns the most recent pipeline run's scores.

### Frontend

React 18 + Vite + Tailwind. All API calls go through `frontend/src/lib/api.js`. Data fetching uses custom hooks (`useMPs`, `useMP`, `useLeaderboard`) that return `{ loading, data, error }`. Vite proxies `/api/v1/*` to `localhost:8000`, so no CORS issues in dev. The backend CORS config hardcodes `localhost:5173`.

## Key Conventions

- All DB queries use async SQLAlchemy: `await session.execute(select(...))` — never `session.query()`
- Session is always injected via `Depends(get_session)` — never instantiated manually in routes
- `store_agent.py` detects MySQL vs PostgreSQL at runtime for upsert dialect (`on_duplicate_key_update` vs `on_conflict_do_update`)
- HTML cache (`data/cache/`) is checked before fetching; pass `force_refresh=True` to bypass it
- The scraper index parser (`parse_index`) uses anchor tag scanning and is separate from the per-MP parser (`parse_mp_page`)

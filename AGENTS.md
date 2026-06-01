# MPPD Agent Instructions

**MP Scorer** is a full-stack civic accountability web app tracking Indian parliamentary performance. This document helps AI agents quickly understand the codebase structure, build process, and conventions.

## Quick Start

### Prerequisites
- **Python 3.11+** (not 3.13; ABI incompatibility with pydantic-core)
- **MySQL 5.7+** or MariaDB (not SQLite)
- **Node.js 18+** with npm

### Environment Setup
1. Copy `.env.example` to `.env` and set `DATABASE_URL`
2. Backend: `pip install -r backend/requirements.txt`
3. Frontend: `cd frontend && npm install`

### Run Services
- **Backend**: `.venv311/Scripts/python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000`
- **Frontend**: `cd frontend && npm run dev` (runs on port 5173)
- **Database migrations**: `python -m alembic upgrade head` (from project root)

---

## Architecture Overview

### Stack
- **Backend**: FastAPI with async SQLAlchemy + asyncmy driver
- **Database**: MySQL with Alembic migrations (4 tables: mp_profiles, mp_raw_data, mp_scores, pipeline_runs)
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Data pipeline**: LangGraph-orchestrated agents (scraper → MPLADS → scoring → storage)

### Key Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/mps` | Paginated MP list with filters (party, is_minister, sort, direction) |
| GET | `/api/v1/mps/{slug}` | Individual MP profile with scores and raw data |
| GET | `/api/v1/mps/leaderboard` | Top/bottom ranked MPs by metric |
| POST | `/api/v1/pipeline/run` | Trigger async data refresh pipeline |
| GET | `/api/v1/pipeline/status/{run_id}` | Poll pipeline job status |

### Data Model
```
MPProfile (id, name, prs_slug, constituency, state, party, is_minister, is_speaker)
  ├─ MPRawData (attendance_pct, questions_count, debates_count, pmb_count, mplads_utilization)
  └─ MPScore (peer_group, attendance/questions/debates/pmb_score, *_rank, total_peers)
```

---

## File Organization

### Backend Structure
```
backend/
├── api/
│   ├── main.py              ← FastAPI app, route registration, CORS config
│   ├── routes/
│   │   ├── mps.py           ← MP data endpoints (complex joins, filtering)
│   │   └── pipeline.py      ← Pipeline orchestration endpoints
│   └── schemas.py           ← Pydantic response models
├── db/
│   ├── models.py            ← SQLAlchemy ORM models (all 4 tables)
│   ├── session.py           ← AsyncSessionLocal + get_session() dependency
│   └── migrations/          ← Alembic versioning
├── agents/
│   ├── orchestrator.py      ← Pipeline coordinator, calls all agents
│   ├── prs_scraper_agent.py ← Fetches from prsindia.org, caches HTML
│   ├── mplads_agent.py      ← Enriches with constituency fund data
│   └── scoring_agent.py     ← Calculates peer-normalized scores
├── core/
│   └── config.py            ← Pydantic settings from .env
└── requirements.txt         ← Python dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── App.jsx              ← React Router setup (3 pages)
│   ├── pages/
│   │   ├── Home.jsx         ← MP listing, search, filters
│   │   ├── MPProfile.jsx    ← Individual MP detail view
│   │   └── LeaderboardPage.jsx ← Top/bottom ranked MPs
│   ├── components/
│   │   ├── MPCard.jsx       ← Reusable MP card component
│   │   ├── ScoreBar.jsx     ← Score visualization (0-10)
│   │   ├── FilterBar.jsx    ← Party/minister/sort filters
│   │   └── ...
│   ├── hooks/
│   │   ├── useMPs.js        ← Fetch paginated MP list
│   │   ├── useMP.js         ← Fetch single MP profile
│   │   └── useLeaderboard.js ← Fetch ranked MPs
│   ├── lib/api.js           ← Axios client, all API functions
│   └── index.css            ← Tailwind imports
├── package.json             ← npm scripts (dev, build, preview)
└── vite.config.js           ← Dev server proxy to localhost:8000
```

---

## Common Tasks

### 1. Adding a New API Endpoint
1. **Define schema** in `backend/api/schemas.py` (Pydantic BaseModel)
2. **Add route** in `backend/api/routes/mps.py` or create new file in routes/
3. **Use dependency injection**: `session: AsyncSession = Depends(get_session)`
4. **Query with SQLAlchemy async**: `await session.execute(select(...))`
5. **Test via** `curl http://localhost:8000/api/v1/...` or frontend

### 2. Modifying Database Schema
1. Update model in `backend/db/models.py`
2. Create migration: `python -m alembic revision --autogenerate -m "description"`
3. Apply migration: `python -m alembic upgrade head`
4. **Important**: Restart backend after schema changes

### 3. Building UI Components
1. Create component in `frontend/src/components/`
2. Use existing hooks (`useMPs`, `useMP`, `useLeaderboard`) to fetch data
3. Style with Tailwind CSS classes
4. Import in pages or other components
5. **Hot reload** automatically via Vite dev server

### 4. Triggering Data Pipeline
- Frontend: `POST /api/v1/pipeline/run` with `{"force_refresh": false}`
- Polling: `GET /api/v1/pipeline/status/{run_id}` every 2 seconds
- Pipeline stages: Scraper → MPLADS → Scoring → Storage (async, can take 30+ seconds)

---

## Key Implementation Details

### Async Database Patterns
- **Never use `session.query()`** — use `await session.execute(select(...))`
- **Always inject session** via `Depends(get_session)` for automatic cleanup
- **Expire on commit = False** configured so detached objects still work after query
- **MySQL-specific**: `.nulls_last()` doesn't work; use `.order_by(column.desc())` then sort in Python if needed

### Scoring Algorithm
- **Peer groups**: Minister vs. Non-minister (separate ranking pools)
- **Metrics**: Attendance %, questions asked, debates participated, private members bills sponsored
- **Ranking**: 1-10 scale within peer group (1 = lowest performer in group)
- **Code**: [backend/agents/scoring_agent.py](backend/agents/scoring_agent.py) uses pandas for stratification

### Frontend API Requests
- **Base URL**: `/api/v1` (proxied by Vite to localhost:8000)
- **Timeout**: 10 seconds per request
- **Error handling**: Hooks return `{ loading, data, error, summary }`
- **Pagination**: `/mps?page=1&limit=20` returns `{ total, page, limit, results }`

### Route Ordering (Important!)
In [backend/api/routes/mps.py](backend/api/routes/mps.py):
- Specific routes (`/leaderboard`, `/stats/summary`) **must come before** generic `/{slug}` 
- Otherwise `/{slug}` catches all requests and returns 404 for specific routes

---

## Common Pitfalls & Solutions

| Issue | Solution |
|-------|----------|
| **Import errors** | Run from project root; use `python -m uvicorn...` not direct python call |
| **Database connection refused** | Check `.env` DATABASE_URL, MySQL service running, credentials correct |
| **Async test failures** | Always use `await` with async functions; use `asyncio.run()` in scripts |
| **Frontend blank page** | Check Vite dev server is running on 5173; check browser console for fetch errors |
| **Pipeline returns 404** | Backend routes are ordered wrong — move specific routes before `/{slug}` |
| **Scores showing as "—"** | Trigger `/pipeline/run` first; scores only populated after pipeline completes |
| **CORS errors** | Check [main.py](backend/api/main.py) CORS config; hardcoded to localhost:5173 |

---

## Entry Points for Different Tasks

### Debugging API Issues
1. Start: [backend/api/routes/mps.py](backend/api/routes/mps.py)
2. Then: [backend/db/models.py](backend/db/models.py) (schema/relationships)
3. Then: [backend/core/config.py](backend/core/config.py) (database URL)

### Debugging Frontend Issues
1. Start: [frontend/src/lib/api.js](frontend/src/lib/api.js) (API client config)
2. Then: [frontend/src/hooks/](frontend/src/hooks/) (data fetching logic)
3. Then: [frontend/src/pages/](frontend/src/pages/) (page components)

### Data Pipeline Issues
1. Start: [backend/agents/orchestrator.py](backend/agents/orchestrator.py) (coordinator)
2. Then: [backend/agents/prs_scraper_agent.py](backend/agents/prs_scraper_agent.py) (if scraper issue)
3. Then: [backend/agents/scoring_agent.py](backend/agents/scoring_agent.py) (if scoring issue)

### Database Schema Issues
1. Start: [backend/db/models.py](backend/db/models.py) (ORM definition)
2. Then: [backend/alembic/versions/](backend/alembic/versions/) (migration scripts)
3. Then: [backend/db/session.py](backend/db/session.py) (session config)

---

## Testing Commands

```bash
# Backend: Check server is running
curl http://localhost:8000/api/v1/mps?limit=2

# Frontend: Check dev server
curl http://localhost:5173

# Database: Check connection
python -c "import backend.db.session; print('OK')"

# Pipeline: Trigger data refresh
curl -X POST http://localhost:8000/api/v1/pipeline/run -H "Content-Type: application/json" -d '{"force_refresh": false}'
```

---

## Additional Resources

- [README.md](README.md) — Project overview and quick start
- `.env.example` — Environment variables template
- Backend requirements: [backend/requirements.txt](backend/requirements.txt)
- Frontend package config: [frontend/package.json](frontend/package.json)

---

## When to Ask for Clarification

If you encounter:
- **Unknown dependencies**: Check `requirements.txt` or `package.json` first
- **Unclear naming conventions**: Backend uses snake_case functions, PascalCase classes; frontend uses PascalCase files
- **Complex queries**: See [backend/api/routes/mps.py](backend/api/routes/mps.py) for SQLAlchemy + async pattern examples
- **State management confusion**: Frontend uses custom hooks + React Context (not Redux); see [frontend/src/hooks/](frontend/src/hooks/) examples

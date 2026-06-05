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
# WARNING: there are two Alembic heads — always specify the revision explicitly, never use "head"
cd backend && python -m alembic upgrade 0005
cd backend && python -m alembic revision -m "description"

# Quick smoke tests
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/mps?limit=2"

# Trigger pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/run -H "Content-Type: application/json" -d '{"force_refresh": false}'
```

## Architecture

### Data Pipeline (the core of the app)

`POST /pipeline/run` fires an async background job. The orchestrator in `backend/agents/orchestrator.py` runs four agents in sequence, passing a shared `state` dict between them:

1. **prs_scraper_agent** — Downloads the 18th LS CSV from `prsindia.org/mptrack/download`. Parses it with pandas (`parse_csv_download`). Also reads `data/cache/{slug}.html` for each MP (pre-fetched HTML pages) to extract the profile image URL via regex on `/files/mptrack/18-lok-sabha/profile_image/{id}.jpg`.

2. **mplads_agent** — Fetches MPLADS constituency fund utilization from data.gov.in API (requires `DATAGOV_API_KEY`). Matches MP names via fuzzy string matching (rapidfuzz). Gracefully skips if key is absent.

3. **scoring_agent** — Uses pandas to compute 0–10 percentile scores within two peer groups: `"minister"` and `"non-minister"`. Ministers are excluded from questions/debates/PMB ranking (those metrics are NULL for them). Only attendance is scored across all MPs.

4. **store_agent** — Upserts `mp_profiles` on `prs_slug` uniqueness, then inserts new rows into `mp_raw_data` and `mp_scores` (append-only; latest scores are found via `MAX(scored_at)` subquery).

### Database

MySQL only (driver: `asyncmy`). Seven tables:
- `mp_profiles` — one row per MP; fields include `education`, `age`, `gender`, `terms`, `is_minister`, `is_speaker`, `is_loa`, `image_url`
- `mp_raw_data` — append-only scrape results per pipeline run; includes national/state averages per metric
- `mp_scores` — append-only peer-normalized scores per pipeline run
- `pipeline_runs` — job tracking (shared between Phase 1 and Phase 2 pipelines)
- `mp_affidavits` — one row per MyNeta winner; upsert key is `myneta_candidate_id`
- `mp_criminal_cases` — one row per criminal case per MP; FK → `mp_affidavits.id`
- `mp_asset_history` — prior-election asset declarations; FK → `mp_affidavits.id`

Phase 2 tables are **not managed by Alembic** — they are created automatically via `Base.metadata.create_all()` on app startup. Do not write Alembic migrations for them.

Migration files live in `backend/db/migrations/versions/`. Alembic config is `backend/alembic.ini`; the `script_location` is relative so alembic must be invoked from `backend/`.

### Phase 2 — MyNeta Integrity Pipeline

`run_integrity_scrape.bat` (or `asyncio.run(run())` directly) runs a standalone pipeline:

1. **scraper/myneta.py** — fetches winners index (485 elected MPs from MyNeta), then fetches each candidate page. Caches raw HTML to `data/cache/myneta/{id}.html`.
2. **agents/extraction_agent.py** — sends cleaned page text to Groq (`llama-3.1-8b-instant`, temp=0) and validates the JSON response against `AffidavitExtraction` Pydantic schema. Retries up to 3 times; sleeps on 429 rate-limit errors using the retry-after from the error message.
3. **agents/myneta_pipeline.py** — orchestrates the full run: fetch → extract → rapidfuzz name-match against `mp_profiles` → upsert to `mp_affidavits`. Writes unmatched names to `data/unmatched_candidates.log`.

**Groq free-tier limits:** 6,000 TPM and 500,000 TPD. Each extraction uses ~4,000–5,000 tokens. The daily cap allows ~100 extractions before hitting the limit. Re-running after midnight UTC resumes from where it left off (upsert skips already-successful rows is NOT automatic — all rows are re-extracted on re-run unless you filter by `extraction_success=True` manually).

**Matching:** rapidfuzz `token_sort_ratio` ≥85 → `high`, 70–84 → `low`, <70 → `none`. Low/none cases logged to `data/unmatched_candidates.log` and retrievable via `GET /api/v1/integrity/unmatched`.

### Phase 2 API Routes

All under `/api/v1/integrity`. **Route ordering is critical** — `/summary`, `/unmatched`, `/scrape`, `/scrape/status/{run_id}` must all be declared before `/{slug}`.

- `GET /integrity/{slug}` — full integrity data for one MP (criminal cases, assets, history, disclaimer)
- `GET /integrity/summary` — aggregate stats across all MPs
- `POST /integrity/scrape` — triggers pipeline as FastAPI BackgroundTask
- `GET /integrity/scrape/status/{run_id}` — poll pipeline progress
- `GET /integrity/unmatched` — MPs where name match was low-confidence or failed

Every response that includes criminal or asset data must include the `disclaimer` field (ADR/myneta.info attribution).

### API Routes (Phase 1)

All routes under `/api/v1`. **Route ordering in `mps.py` is critical**: `/leaderboard` and `/stats/summary` must be declared before `/{slug}` or FastAPI will match them as slug values.

Scores are joined via a `MAX(scored_at)` subquery so the API always returns the most recent pipeline run's scores.

`GET /mps` accepts: `party`, `state`, `gender`, `is_minister`, `is_speaker`, `is_loa`, `has_criminal_cases`, `has_serious_cases`, `is_convicted`, `is_crorepati` (bools), `terms` (exact term count), `terms_min` (≥, used for the "5+ terms" bucket), `search`, `sort`, `direction`, `page`, `limit`. Integrity filters (`has_*`, `is_convicted`, `is_crorepati`) run against the `_affidavit_aggregate()` subquery (one row per `mp_id`) that's outer-joined into the list query.

### Derived Scores & Asset Growth (`backend/core/`)

Pure, dependency-free helpers (well unit-tested by example) consumed by the API routes — NOT part of the scraping pipeline:

- **`core/scoring.py` → `compute_clean_record_score(serious, minor)`** — absolute 0–100 integrity score from an MP's *convictions* (not pending cases). Starts at 100; major conviction −50 (first 3) / −25 (4th+); minor −20 (first 3) / −10 (4th+); floored at 0. Major = `convictions_serious`, minor = `total_convictions − convictions_serious`. Null when the MP has no affidavit.
- **`core/assets.py`** — `asset_growth` (% change since most recent prior election), `asset_growth_first` (% change since earliest declaration), and `asset_series` (chronological `[{year, label, assets}]` for the sparkline). `election_label` is free-text from the LLM, so a 4-digit year is regex-parsed out of it to order declarations. `CURRENT_ELECTION_YEAR = 2024`: history entries at/after 2024 are dropped (the extraction sometimes echoes the current declaration into history → would otherwise compare 2024→2024). All asset-growth output is **gated on `terms > 1`** in the routes — first-time MPs show no growth/graph (the user explicitly wants this).

**`total_score`** (on `MPSummary`) is the mean of an MP's available 0–100 metrics — attendance/questions/debates/pmb scores **plus `clean_record_score`**. Because `clean_record_score` is derived in Python (not a SQL column), sorting by `total_score` can't be done in SQL: the `sort=total_score` branch in `list_mps` fetches all matching rows, builds summaries, then sorts & paginates in-process (fine at ~550 rows). MPs with no scored metrics sort last in both directions. The frontend card donut reuses `mp.total_score` when present, else recomputes client-side (e.g. the leaderboard endpoint doesn't supply it).

`_summary_from_row()` is the single builder shared by the SQL-sorted and Python-sorted paths; `_asset_growth_map()` fetches affidavit totals + asset history for the page's MPs in two scans and computes growth/series per `mp_id` (can't pick "most recent prior" in SQL with free-text labels).

### Frontend

React 18 + Vite + Tailwind. All API calls go through `frontend/src/lib/api.js`. Data fetching uses custom hooks (`useMPs`, `useMP`, `useLeaderboard`) that return `{ loading, data, error }`. Vite proxies `/api/v1/*` to `localhost:8000`, so no CORS issues in dev. The backend CORS config hardcodes `localhost:5173` (note: if 5173 is busy Vite uses 5174 — the proxy still works, CORS is irrelevant in dev).

Notable components: `MPCard` (cards on the list page — clean-record bar, integrity chips, and a click-to-expand `AssetTrend` showing a sparkline + since-last/since-first growth), `Sparkline` (dependency-free SVG line chart, shared by card and detail page), `AssetsPanel` (detail-page asset trajectory graph + figures), `FilterBar` (all filters incl. Terms and the Total-score sort), `ScoreBar`/`ScoreRing`.

**When a hook destructures explicit params (`useMPs`), a new filter must be threaded through three places: the hook signature, the `fetchMPs(...)` call, AND the effect dependency array** — otherwise it won't trigger a refetch.

**UI performance gotchas (the user is sensitive to a "shaky" UI — take these seriously):**
- **No `backdrop-blur` on sticky or scroll-overlapping elements.** A sticky `backdrop-blur` re-blurs everything beneath it every scroll frame → judder on trackpads. The navbar and pagination bar use near-opaque `bg-white/95` instead.
- **The page background gradient lives on a fixed, GPU-composited `body::before` layer** (`index.css`), NOT `background-attachment: fixed` (which repaints the gradient every scroll frame).
- **`scrollbar-gutter: stable` on `html` + `overflow-x: clip` on `body`** (`index.css`) — reserves the scrollbar's width so the layout doesn't lurch sideways when result height changes toggle the scrollbar on/off. Use `clip` not `hidden` (hidden would make `body` a scroll container and break the sticky navbar).
- **No `translate` on card hover** — lifting the card moved it out from under the cursor near edges, causing hover/un-hover oscillation. Cards use shadow/border hover only. The `fade-up` keyframe is opacity-only (no `translateY`) so the grid doesn't slide on every filter change.
- **Tailwind `group` is not auto-scoped:** a tooltip using `group-hover:` fires when ANY ancestor `.group` is hovered. The card root is `.group`, so the `ScoreBar` info-tooltip must use a **named** group (`group/info` + `group-hover/info:`) or every tooltip on the card pops at once.

## Key Conventions

- All DB queries use async SQLAlchemy: `await session.execute(select(...))` — never `session.query()`
- Session is always injected via `Depends(get_session)` — never instantiated manually in routes
- `store_agent.py` detects MySQL vs PostgreSQL at runtime for upsert dialect (`on_duplicate_key_update` vs `on_conflict_do_update`); `myneta_pipeline.py` uses the same pattern
- HTML cache (`data/cache/`) holds 544 pre-fetched MP pages used only for image URL extraction; pass `force_refresh=True` to re-download the CSV
- MyNeta HTML cache lives in `data/cache/myneta/` (separate from PRS cache); both dirs are covered by `data/` in `.gitignore`
- **Alembic has two heads** (`0002` orphan + `0005`): never run `alembic upgrade head` — always specify the revision, e.g. `alembic upgrade 0005`
- Phase 2 tables (`mp_affidavits`, `mp_criminal_cases`, `mp_asset_history`) are NOT in Alembic — created by `Base.metadata.create_all()` on startup
- If an MP's PRS slug changes between pipeline runs, a duplicate `mp_profiles` row is created (upsert key is `prs_slug`); delete the stale row manually
- `mp_affidavits` upsert key is `myneta_candidate_id`; re-running the pipeline overwrites all fields including `extraction_success`

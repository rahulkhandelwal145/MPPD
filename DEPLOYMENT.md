# Deployment Guide

All deployment uses Docker Compose. The stack is three containers:
`db` (MySQL 8), `backend` (Python/uvicorn), `frontend` (nginx serving the React build).

---

## Prerequisites (one-time, on the server)

### Oracle Linux (8 or 9)

```bash
# Add the official Docker CE repo (Oracle Linux is RHEL-compatible)
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo

# Install Docker Engine + Compose plugin
sudo dnf install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# Start Docker and enable it on boot
sudo systemctl enable --now docker

# Allow your user to run docker without sudo (log out and back in after this)
sudo usermod -aG docker $USER

# Git
sudo dnf install -y git
```

> **Oracle Linux 8 note:** if `dnf config-manager` is missing, install it first:
> `sudo dnf install -y 'dnf-command(config-manager)'`

### Ubuntu / Debian

```bash
# Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # log out and back in after this

# Git
sudo apt-get install -y git
```

---

## Initial Deployment

### 1. Clone the repo

```bash
git clone https://github.com/rahulkhandelwal145/MPPD.git
cd MPPD
```

### 2. Create `.env`

Copy the example and fill in real values:

```bash
cp .env.docker.example .env
nano .env
```

Required fields:

```env
# Strong password — avoid % and # (they break URL encoding)
DB_ROOT_PASSWORD=YourStrongPassword

# Use the same password here; host must be "db" (the compose service name)
DATABASE_URL=mysql+asyncmy://root:YourStrongPassword@db:3306/mpscorer

# Groq API key for LLM features (statement monitor, integrity extraction)
# Get one free at console.groq.com
GROQ_API_KEY=gsk_...

# data.gov.in API key for MPLADS constituency fund data (optional)
DATAGOV_API_KEY=

LLM_PROVIDER=groq
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1:8b
DEBUG=false
```

### 3. Upload the HTML cache

The `data/cache/` directory holds 544 pre-fetched MP profile HTML pages used
for image URL extraction. These are not in git (too large). Copy them from
your local machine to the server:

```bash
# Run this from your local machine, not the server
rsync -az --progress data/cache/ user@your-server:/path/to/MPPD/data/cache/
```

If you skip this step the pipeline still works — MPs will just have no profile
images until the cache is re-fetched with `force_refresh=true`.

### 4. Build and start all containers

```bash
docker compose up --build -d
```

This will:
- Pull MySQL 8, node:20-alpine, nginx:alpine base images
- Build the backend (installs Python deps) and frontend (runs `npm run build`)
- Start all three containers
- The backend entrypoint automatically runs Alembic migrations before uvicorn starts
- Non-Alembic tables (`mp_mplads`, `mp_news_articles`, `mp_statements`,
  `mp_discrepancy_reports`) are created on first startup via `Base.metadata.create_all()`

### 5. Verify everything is up

```bash
docker compose ps
curl http://localhost:8000/api/v1/health   # {"status":"ok","debug":false}
curl http://localhost/                     # 200 from nginx
```

### 6. Seed the database

The database starts empty. Run the pipelines in order:

#### a) PRS parliamentary performance data (required — the core dataset)

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{"force_refresh": false}'
```

This downloads the PRS 18th Lok Sabha CSV, parses it, scores all 543 MPs, and
stores everything. Takes ~30 seconds. Poll status:

```bash
# Use the run_id from the POST response
curl http://localhost:8000/api/v1/pipeline/status/<run_id>
```

#### b) MyNeta integrity data — criminal cases & assets (optional)

Runs inside the backend container. Uses Groq (free tier: ~100 MPs/day):

```bash
docker compose exec backend bash -c "
  cd /app && python -m backend.agents.myneta_pipeline
"
```

Re-run on subsequent days to continue where it left off (up to the Groq daily
cap). Unmatched MP names are logged to `data/unmatched_candidates.log`.

#### c) MPLADS constituency fund data (optional, needs DATAGOV_API_KEY)

Triggered automatically as part of the main pipeline run (step a). If you add
`DATAGOV_API_KEY` later, just re-run the pipeline.

#### d) Public Statement Monitor (optional, needs GROQ_API_KEY)

Fetches news, extracts quotes, classifies statements for all 543 MPs.
Takes 4–5 hours for a full run:

```bash
curl -X POST http://localhost:8000/api/v1/statements/run \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'    # omit limit to run all MPs
```

Or run a specific MP by slug:

```bash
curl -X POST http://localhost:8000/api/v1/statements/run \
  -H "Content-Type: application/json" \
  -d '{"slug": "narendra-modi"}'
```

After the initial run, the statement monitor reruns automatically every
Sunday at 02:00 via APScheduler.

---

## Redeployment After Code Changes

```bash
# On the server
cd /path/to/MPPD

# Pull latest code
git pull origin master

# Rebuild and restart only the app containers (db keeps running untouched)
docker compose build backend frontend
docker compose up -d backend frontend
```

The backend entrypoint re-runs `alembic upgrade 0005` on every start — safe to
run repeatedly (idempotent). New non-Alembic tables are created with
`checkfirst=True` so existing tables are never touched.

**No manual migration steps are needed** for new non-Alembic tables
(`mp_mplads`, `mp_news_articles`, `mp_statements`, `mp_discrepancy_reports`).
They are created automatically on startup.

---

## Checking Logs

```bash
# Live backend logs (uvicorn + app output)
docker compose logs -f backend

# Live frontend logs (nginx access/error)
docker compose logs -f frontend

# Statement monitor log (written to the host-mounted logs/ directory)
tail -f logs/statement_monitor.log
```

---

## Viewing Discrepancy Reports

User-submitted data corrections are stored in `mp_discrepancy_reports`.
Query them directly from the backend:

```bash
# All reports, newest first
curl http://localhost:8000/api/v1/reports

# Only new (unreviewed) reports
curl "http://localhost:8000/api/v1/reports?status=new"
```

Or browse the interactive API docs: `http://your-server:8000/api/v1/docs`

---

## Data Persistence

| What | Where | Survives rebuild? |
|---|---|---|
| MySQL data | `mysql_data` Docker volume | Yes |
| MP HTML cache | `./data/cache/` (bind mount) | Yes (on host) |
| MyNeta HTML cache | `./data/cache/myneta/` (bind mount) | Yes (on host) |
| Statement monitor log | `./logs/` (bind mount) | Yes (on host) |
| Unmatched MP names | `./data/unmatched_candidates.log` | Yes (on host) |

> The `mysql_data` volume is **not deleted** by `docker compose down` —
> only by `docker compose down -v`. Never run `-v` in production.

---

## Alembic Note

There are two Alembic heads in the migration history. The entrypoint always
runs `alembic upgrade 0005` explicitly — **never `alembic upgrade head`**
as that will error on the branched history.

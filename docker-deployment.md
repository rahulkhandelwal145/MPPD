# Docker Deployment Guide

## Prerequisites

- Docker + Docker Compose installed
- MySQL client (`mysqldump`) available for data seeding
- A `.env` file at the project root (copy from `.env.docker.example`)

---

## Environment Variables

Create `.env` at the project root before starting:

```env
DB_ROOT_PASSWORD=yourpassword          # No # or % — causes .env parsing issues
DATABASE_URL=mysql+asyncmy://root:yourpassword@db:3306/mpscorer
GROQ_API_KEY=your_groq_key
DATAGOV_API_KEY=                       # Optional
LLM_PROVIDER=groq                      # "groq" or "ollama"
OLLAMA_BASE_URL=http://host.docker.internal:11434   # If using local Ollama
OLLAMA_MODEL=llama3.1:8b
DEBUG=false
```

> **Important:** `DB_ROOT_PASSWORD` and the password in `DATABASE_URL` must match exactly.
> The root `.env` is gitignored — never commit it.

---

## Running Locally

```bash
# Start all containers (db + backend + frontend)
docker compose up -d --build

# App is available at http://localhost
# Backend direct access: http://localhost:8000
# MySQL: localhost:3307
```

### Seed data from local MySQL (first run only)

Run from your local Windows machine:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" `
    -u root "-pYourLocalPassword" -h 127.0.0.1 mpscorer `
  | docker exec -i mppd-db-1 mysql -u root -pYourDockerPassword mpscorer
```

Container is named `mppd-db-1` when running locally (project folder = `MPPD`).

### Stopping

```bash
docker compose down          # Stop containers, keep data volume
docker compose down -v       # Stop containers AND delete DB volume (data lost)
```

---

## Deploying to a Cloud VM (Azure / GCP / AWS)

### 1. Provision a VM

| Provider | Free tier | Shape |
|---|---|---|
| Azure | Pay-as-you-go / student credit | B1s (1 vCPU, 1 GB RAM) |
| Google Cloud | Always Free | e2-micro (us-central1/us-west1/us-east1) |
| AWS | 12 months free | t2.micro |
| Oracle Cloud | Always Free | VM.Standard.A1.Flex (ARM, up to 24 GB) |

Minimum recommended: **2 GB RAM**. Add swap if on 1 GB (see below).

### 2. SSH into the VM

```bash
ssh <username>@<vm-public-ip>
```

### 3. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### 4. Add swap (required on 1 GB RAM VMs)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 5. Clone the repo

```bash
sudo git clone https://<username>:<GITHUB_TOKEN>@github.com/rahulkhandelwal145/MPPD.git /app
cd /app
```

### 6. Set up secrets

```bash
cp .env.docker.example .env
nano .env   # Fill in DB_ROOT_PASSWORD, DATABASE_URL, GROQ_API_KEY
```

### 7. Open firewall ports

**Azure:** Portal → VM → Networking → Add inbound port rule → TCP 80, 443

**Google Cloud:** VPC Network → Firewall → Create Rule → TCP 80, 443

**AWS:** EC2 → Security Groups → Inbound Rules → TCP 80, 443

Also run on the VM (required on Oracle Cloud):
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### 8. Start the stack

```bash
cd /app
docker compose up -d --build
```

First build takes ~10 minutes on a small VM.

### 9. Seed data from local machine

Run from your local Windows machine (PowerShell):

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe" `
    -u root "-pYourLocalPassword" -h 127.0.0.1 mpscorer `
  | ssh <username>@<vm-ip> "docker exec -i app-db-1 mysql -u root -pYourDockerPassword mpscorer"
```

> Container is named `app-db-1` on the server (project folder = `/app`).

---

## HTTPS with Caddy (optional)

Once a domain points to your VM's IP:

```bash
sudo apt install -y caddy
sudo nano /etc/caddy/Caddyfile
```

```
yourdomain.com {
    reverse_proxy localhost:80
}
```

```bash
sudo systemctl restart caddy
```

Caddy auto-provisions a Let's Encrypt certificate. No further config needed.

---

## Useful Commands

```bash
# View logs
docker compose logs -f backend
docker compose logs -f db

# Restart a single service
docker compose restart backend

# Rebuild after code changes
docker compose up -d --build backend

# Check container status
docker compose ps

# Open a MySQL shell inside the container
docker exec -it app-db-1 mysql -u root -p
```

---

## Architecture

```
Browser
  └── nginx (port 80)  ← frontend container
        ├── /          → serves built React static files
        └── /api/      → proxied to backend:8000
              └── FastAPI (port 8000)  ← backend container
                    └── MySQL (port 3306)  ← db container (volume: mysql_data)
```

Alembic migrations run automatically on backend startup via `entrypoint.sh`.
Phase 2/3/4 tables (`mp_affidavits`, `mp_mplads`, `mp_news_articles`, `mp_statements`) are created by `Base.metadata.create_all()` on startup — not managed by Alembic.

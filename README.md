# ReconX Elite

ReconX Elite is a full-stack bug bounty reconnaissance platform built around FastAPI, Celery, Redis, PostgreSQL, and React. It manages authenticated target tracking, staged recon scans, attack-surface prioritization, JavaScript intelligence, heuristic correlation, notes, bookmarks, schedules, notifications, and report downloads from one monorepo.

## Architecture

```text
frontend (React/Vite, static container)
  -> backend (FastAPI)
     -> PostgreSQL
     -> Redis
     -> Celery worker
        -> subfinder / httpx / gau / nuclei
```

## Key capabilities

- JWT access + refresh auth with automatic frontend refresh handling.
- Target management with strict domain normalization.
- Scan pipeline staged as `subfinder -> httpx -> gau -> nuclei`.
- Soft-fail enrichment, JavaScript analysis, heuristic correlation, and ranked attack-path generation.
- Recon data for subdomains, endpoints, vulnerabilities, JavaScript assets, and attack paths.
- Notes, bookmarks, scheduled scans, notifications, scan diffs, and downloadable reports.
- Docker Compose stack with production-style frontend serving and Alembic migrations.

## Repository layout

```text
.
├── backend/
│   ├── alembic/
│   ├── app/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── Dockerfile
├── worker/
├── docker-compose.yml
└── .env.example
```

## Required tools

ReconX Elite expects these CLI tools inside the backend and worker runtime:

- `subfinder`
- `httpx`
- `gau`
- `nuclei`

The provided Dockerfiles install pinned versions of all four tools.

## Environment setup

1. Copy the root example file.
2. Adjust secrets and origins for your environment.

```bash
cp .env.example .env
```

Important variables:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `CORS_ALLOWED_ORIGINS`
- `SCAN_THROTTLE_SECONDS`
- `VITE_API_BASE_URL`

## Local backend workflow

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run the worker in a second shell:

```bash
cd backend
.venv\Scripts\activate
celery -A app.tasks.celery_app.celery_app worker --loglevel=info
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Docker usage

```bash
cp .env.example .env
docker compose up --build
```

Expected services:

- Backend API: [http://localhost:8000](http://localhost:8000)
- Frontend: [http://localhost:5173](http://localhost:5173)
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Both backend and worker run `alembic upgrade head` on container start so fresh databases pick up the baseline schema automatically.

## API routes

Auth:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`

Targets:

- `POST /targets`
- `GET /targets`
- `GET /targets/{id}`
- `PUT /targets/{id}`

Scans:

- `POST /scan/{target_id}`
- `POST /scan/{target_id}/config`
- `GET /scans/{scan_id}`

Bookmarks / notes / schedules:

- `GET /bookmarks`
- `POST /bookmarks`
- `DELETE /bookmarks/{id}`
- `PUT /vulnerabilities/{id}`
- `GET /schedules`
- `POST /schedules`
- `PUT /schedules/{id}`
- `DELETE /schedules/{id}`

Reports and notifications:

- `GET /notifications`
- `PUT /notifications/{id}/read`
- `GET /reports/{target_id}/json`
- `GET /reports/{target_id}/pdf`

Health:

- `GET /health`

Interactive OpenAPI docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Testing

Backend unit checks:

```bash
cd backend
python -m unittest discover -s tests
```

Recommended smoke checks after startup:

- Register, login, and refresh a user session.
- Create a target and verify `GET /targets`.
- Trigger default and configured scans.
- Poll `GET /scans/{scan_id}` until completion.
- Verify bookmarks, notes, schedules, reports, and notifications.

## Legal notice

Use ReconX Elite only against domains, subdomains, applications, and infrastructure you own or are explicitly authorized to assess. Running recon or vulnerability tooling without permission can violate law, platform policy, or contractual scope.

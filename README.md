# FIBER PON Tracker App

A comprehensive web application for training and tracking Project Managers and Site Managers on FiberTime sites. The app tracks PONs (Passive Optical Networks), tasks, certificate acceptance checks, stringing, photos, SMMEs, stock, and invoicing with evidence enforcement, geofencing/EXIF validation, and auto-status computation.

## What’s new (Upgrades and Changes)

- Backend: Introduced a new FastAPI (Python) backend with PostgreSQL + SQLAlchemy
- Data store: Moved from MongoDB to PostgreSQL (PostGIS-enabled container in dev)
- Media storage: S3-compatible storage via MinIO for photo evidence
- Background jobs: APScheduler for SLA scans, photo revalidation, and weekly reports
- Modules: Added organizations, contracts, assignments, work queue, and fiber technical data
- NMS integration: HMAC-validated webhook endpoints for network events
- Security: CORS allowlist and standardized secret names for staging/production
- Terminology: Renamed CAC to Certificate Acceptance
- Client: Upgraded to React 19, React Router 7, and MUI 7
- Infra: Added Docker Compose for Postgres/PostGIS, Redis, MinIO, and MailHog
- Health: Added `/healthz` and `/readyz` endpoints

## Technology Stack

- Backend (default): FastAPI (Python 3.11+) with SQLAlchemy and PostgreSQL
- Backend (legacy): Node.js with Express.js (MongoDB)
- Frontend: React with Material UI (MUI)
- Messaging/Cache: Redis (dev via Docker)
- Object Storage: S3-compatible (MinIO in dev)

## Project Structure

```
├── app/                       # FastAPI backend (current)
│   ├── main.py                # FastAPI app entry
│   ├── core/                  # DB deps, rate limiting, etc.
│   ├── models/                # SQLAlchemy models
│   ├── routers/               # API routers/endpoints
│   ├── services/              # S3, EXIF, PDF, etc.
│   └── scheduler.py           # APScheduler jobs
├── server/                    # Legacy Node/Express backend (MongoDB)
│   ├── routes/, models/, ...
│   └── index.js
├── client/                    # React frontend (CRA)
│   ├── src/
│   └── public/
├── infra/
│   └── docker-compose.yml     # Postgres+PostGIS, Redis, MinIO, MailHog
├── db/
│   └── init/                  # Base schema SQL applied by Postgres container
├── alembic/versions/          # Versioned SQL changes (reference)
└── requirements.txt           # Python dependencies
```

## Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for the React client)
- Docker + Docker Compose (for local infra services)

### Start local infrastructure
```bash
docker compose -f infra/docker-compose.yml up -d
```

This starts PostgreSQL (PostGIS), Redis, MinIO (S3), and MailHog. The Postgres container automatically applies SQL from `db/init` on first startup.

### Backend (FastAPI)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment (examples)
export DATABASE_URL="postgresql+psycopg2://app:app@localhost:5432/app"
export CORS_ALLOW_ORIGINS="http://localhost:3000"
export S3_ENDPOINT="http://localhost:9000"
export S3_REGION="us-east-1"
export S3_BUCKET="fiber-photos"
export S3_ACCESS_KEY="minio"
export S3_SECRET_KEY="minio12345"

# Optional HMAC secrets for webhooks/configs
export NMS_HMAC_SECRET="change-me"
export OXIDIZED_HMAC_SECRET="change-me"

# Run API (http://localhost:8000)
uvicorn app.main:app --reload --port 8000
```

Health checks: `GET /healthz`, `GET /readyz`

### Frontend (React)
```bash
cd client
npm install
npm start
```

- Default dev server: `http://localhost:3000`
- If you are using the FastAPI backend (`:8000`), configure your client to call `http://localhost:8000` (adjust proxy or base URL accordingly).

### Legacy Node backend (optional)
The legacy Express/MongoDB backend in `server/` is kept for reference and migration. It is not required when using the FastAPI backend.

If you need it:
- Requires MongoDB and the env vars `MONGODB_URI`, `JWT_SECRET`
- Start with the existing npm scripts (`npm run server`, `npm run dev`), proxying the React client to `:5000`

## Key API Areas (FastAPI)

Routers mounted in the FastAPI app (non-exhaustive):
- `/tasks` (work queue, SLA handling)
- `/certificate-acceptance` (formerly CAC)
- `/pons-geofence`, `/photos-validate`, `/photos-upload-hook`
- `/assets`, `/spares`, `/configs`, `/maintenance`, `/topology`
- `/devices`, `/incidents`, `/optical`, `/nms-webhook`
- `/rate-cards`, `/pay-sheets`, `/contracts`, `/assignments`
- `/reports`

Notes:
- Role checks are header-based: send `X-Role` (e.g., `ADMIN`, `PM`, `SITE`, `AUDITOR`).
- Some endpoints require `X-Org-Id` for filtering (see `/tasks/work-queue`).
- Webhooks require HMAC headers computed with `NMS_HMAC_SECRET` or `OXIDIZED_HMAC_SECRET`.

## Environment & Secrets

FastAPI backend env vars:
- `DATABASE_URL` (required) — e.g., `postgresql+psycopg2://app:app@localhost:5432/app`
- `CORS_ALLOW_ORIGINS` — CSV list (default `*`)
- `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
- `NMS_HMAC_SECRET`, `OXIDIZED_HMAC_SECRET`

See `docs/secrets.md` for standardized secret names for staging/production.

## Upgrade & Migration Notes

- CAC → Certificate Acceptance
  - Path changed from `/api/cac` (legacy) to `/certificate-acceptance` (FastAPI)
  - Validation now enforces at least one validated photo (EXIF + geofence)
- Backend migration (MongoDB → PostgreSQL)
  - New schema is applied by `db/init` on first container start
  - Versioned SQL references in `alembic/versions`
  - Data migration from MongoDB is not automated; export/transform/import is required
- Client upgrades
  - React 19, React Router 7, MUI 7, Axios 1.x
  - Ensure Node 18+ for dev tooling
- Infra
  - Use the included Docker Compose for Postgres, Redis, MinIO, MailHog

### Suggested migration approach (MongoDB → PostgreSQL)

1. Export from MongoDB collections (`users`, `pons`, `tasks`, `photos`, etc.) to JSON/CSV.
2. Map fields to the SQL schema in `db/init/010_core.sql` and related tables.
3. Write one-off ETL scripts to transform IDs to UUIDs and normalize references.
4. Load data into Postgres in dependency order (organizations → users → pons → tasks → photos ...).
5. Verify with FastAPI endpoints (`/tasks`, `/reports`) and adjust indices as needed.

### Switching backends during transition

- You may run only one backend in production; the FastAPI backend is recommended.
- The client should point to the chosen backend base URL.
- For legacy endpoints parity, consult `server/routes/` vs `app/routers/`.

## Development

- Add new API modules under `app/routers/` and models under `app/models/`
- Background jobs live in `app/scheduler.py` (APScheduler)
- Test webhooks locally with `scripts/test_webhooks.sh`

## License

MIT License — see LICENSE file for details

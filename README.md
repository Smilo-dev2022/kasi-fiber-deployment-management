## Stats SA wards (2021) and SubPlaces (2011) loader

This workspace provides a robust, idempotent pipeline to load:

- Wards (Stats SA 2021)
- SubPlaces (Stats SA 2011), treated as suburbs

It tolerates common field-name variants and will spatially join suburbs to wards when a `WARD_ID` column is missing on suburbs.

### Prerequisites

- PostgreSQL with PostGIS
- `ogr2ogr` (from GDAL)

### Files

- `sql/load_sa_geographies.sql` — core loader: creates targets, loads data, builds indexes
- `scripts/import_sa_geographies.sh` — imports shapefiles to staging, runs the loader

### Usage

```bash
./scripts/import_sa_geographies.sh \
  --pg "postgresql://user:pass@host:5432/dbname" \
  --wards /path/to/wards.shp \
  --suburbs /path/to/suburbs.shp
```

The script will:

- Load `wards.shp` into `public.wards_src`
- Load `suburbs.shp` into `public.suburbs_src`
- Populate `geo_wards` and `geo_suburbs` with normalized columns: `id`, `name`, `ward_id` (for suburbs), and `geom` as WKB
- Create GiST indexes on decoded geometries

### Supported field variants

- Wards: `(WARD_ID, WARD_NAME)` or `(CODE, NAME)` or `(WARDNO, NAME)`
- Suburbs: `(SP_CODE, SP_NAME)` or `(SUB_CODE, SUB_NAME)` or fallback to `(gid, NAME)`

If `WARD_ID` is missing on suburbs, a spatial join assigns wards using intersection.

### Inspecting shapefiles before import

```bash
ogrinfo -so /path/to/wards.shp wards | cat
ogrinfo -so /path/to/suburbs.shp suburbs | cat
```

# FIBER PON Tracker App

A comprehensive web application for training and tracking Project Managers and Site Managers on FiberTime sites. The platform tracks PONs (Passive Optical Networks), tasks, Certificate Acceptance (formerly CAC), stringing, photos, SMMEs, stock, invoicing, and more — with evidence enforcement, geofencing, SLA monitoring, and automated status computation.

## What’s New (Upgrades)

- **Core API added**: FastAPI service (`app/`) with PostgreSQL, SQLAlchemy, and Alembic
- **Infra stack**: Postgres (PostGIS), Redis, MinIO (S3-compatible), Mailhog via `infra/docker-compose.yml`
- **Health checks**: FastAPI exposes `/healthz` and `/readyz`
- **CORS**: Configurable allowlist via `CORS_ALLOW_ORIGINS`
- **S3 integration**: Photo bytes stored via `boto3` with S3-compatible endpoints (`app/services/s3.py`)
- **Background jobs**: APScheduler jobs for SLA scan, photo revalidation, weekly report (`app/scheduler.py`)
- **Renamed CAC**: CAC → Certificate Acceptance (see `alembic/versions/0010_cac_to_certificate_acceptance.py` and `app/routers/certificate_acceptance.py`)
- **Domain expansion**: Organizations, contracts, assignments, incidents, devices, optical tests (OTDR/LSPM), work queue, topology, maintenance, spares, rate cards, pay sheets, reports
- **Legacy Node API retained**: Express + MongoDB service (`server/`) with SLA email monitor and existing routes; CRA client continues to proxy to `:5000`

## Technology Stack

- **Core API**: Python 3.x, FastAPI, SQLAlchemy, Alembic, APScheduler
- **Legacy API**: Node.js (Express), Mongoose, Nodemailer
- **Frontend**: React (CRA) + MUI
- **Datastores**: PostgreSQL (PostGIS), Redis, MongoDB (legacy)
- **Object storage**: S3-compatible (MinIO for local dev)
- **Email**: SMTP via Mailhog (local) or provider via env

## Architecture & Project Structure

```
├── app/                      # FastAPI service (core)
│   ├── main.py               # FastAPI entrypoint (/healthz, /readyz)
│   ├── core/                 # DB deps, rate limiting, etc.
│   ├── routers/              # Modular routers (tasks, incidents, optics, etc.)
│   ├── services/             # Integrations (e.g., S3)
│   ├── scheduler.py          # APScheduler jobs
│   └── schemas/models/...    # Pydantic & SQLAlchemy
├── alembic/                  # Database migrations
├── infra/docker-compose.yml  # Postgres, Redis, MinIO, Mailhog
├── server/                   # Legacy Express API
│   ├── index.js              # Express entrypoint (:5000)
│   ├── jobs/slaMonitor.js    # SLA email monitor
│   └── utils/mailer.js       # SMTP transport
├── client/                   # React frontend (CRA)
└── requirements.txt          # Core API Python deps
```

## Quickstart (Local Development)

### 1) Start infrastructure (Postgres, Redis, MinIO, Mailhog)
```bash
docker compose -f infra/docker-compose.yml up -d
```

- **Postgres**: localhost:5432 (user: `app`, pass: `app`, db: `app`)
- **Redis**: localhost:6379
- **MinIO**: `http://localhost:9000` (console `http://localhost:9001`) — user: `minio`, pass: `minio12345`
- **Mailhog**: SMTP `localhost:1025`, UI `http://localhost:8025`

### 2) Run Core API (FastAPI)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql+psycopg2://app:app@localhost:5432/app"
export CORS_ALLOW_ORIGINS="http://localhost:3000"
export S3_ENDPOINT="http://localhost:9000"
export S3_REGION="us-east-1"
export S3_BUCKET="fiber-photos"
export S3_ACCESS_KEY="minio"
export S3_SECRET_KEY="minio12345"

uvicorn app.main:app --reload --port 8000
```

Run DB migrations (Alembic):
```bash
alembic upgrade head
```

### 3) Run Legacy API (Express)
```bash
npm install
export MONGODB_URI="mongodb://localhost:27017/kasi_fiber_db"  # or your URI
export SMTP_HOST=localhost SMTP_PORT=1025 SMTP_USER=foo SMTP_PASS=bar MAIL_FROM="no-reply@kasi-fiber.local"
npm run server
```

The SLA monitor runs in-process; configure with:
- `DISABLE_SLA_MONITOR=true` to turn off
- `SLA_MONITOR_INTERVAL_MS=60000` to set interval

### 4) Run Frontend (CRA)
```bash
cd client
npm install
npm start
```

The client proxies API calls to `http://localhost:5000` (Express). If you consume the FastAPI directly, point requests to `http://localhost:8000`.

### Environment Variables
Ensure production environment variables are set:
- `CORS_ALLOW_ORIGINS`: Comma-separated allowlist (e.g. `https://app.example.com`)
- `NMS_ALLOW_IPS`: Comma-separated source IPs allowed for webhooks
- `NMS_HMAC_SECRET`: Shared secret used to verify HMAC (`X-Signature`)
- `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
\- Rate limiting (tune per env):
  - FastAPI webhooks (per IP): `WEBHOOK_IP_LIMIT`, `WEBHOOK_IP_WINDOW` (default `60` req / `60` sec)
  - Heavy writes (per org): `HEAVY_ORG_LIMIT`, `HEAVY_ORG_WINDOW` (default `120` req / `60` sec)
  - Heavy writes bypass roles: `HEAVY_ORG_BYPASS_ROLES` (comma-separated; default `NOC`)
  - Express webhook (per IP): `WEBHOOK_IP_LIMIT`, `WEBHOOK_IP_WINDOW` used by `server/routes/nmsWebhook.js`
### Staging/Prod Env Files
Create `.env.staging` and `.env.prod` per ops rollout.

Recommended values:

- Staging:
  - `WEBHOOK_IP_LIMIT=15`, `WEBHOOK_IP_WINDOW=60`
  - `HEAVY_ORG_LIMIT=60`, `HEAVY_ORG_WINDOW=60`, `HEAVY_ORG_BYPASS_ROLES=NOC`
- Production:
  - `WEBHOOK_IP_LIMIT=60`, `WEBHOOK_IP_WINDOW=60`
  - `HEAVY_ORG_LIMIT=120`, `HEAVY_ORG_WINDOW=60`, `HEAVY_ORG_BYPASS_ROLES=NOC`

### Alembic
Run migrations using:

```bash
export $(cat .env.staging | xargs) && alembic upgrade head
```

### MinIO Setup
Bring up infra and configure bucket/lifecycle:

```bash
docker compose -f infra/docker-compose.yml up -d db minio
export $(cat .env.staging | xargs) && python scripts/setup_minio.py
```

- `NODE_ENV=production`
- `MONGODB_URI` (production database)
- `JWT_SECRET` (strong secret key)

## Configuration & Environment

Key environment variables (see also `docs/secrets.md`):

- Core API (FastAPI)
  - `DATABASE_URL` (e.g., `postgresql+psycopg2://app:app@localhost:5432/app`)
  - `CORS_ALLOW_ORIGINS` (comma-separated list or `*`)
  - `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`

- Legacy API (Express)
  - `MONGODB_URI`, `JWT_SECRET`, `PORT` (default 5000)
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURE`, `SMTP_USER`, `SMTP_PASS`, `MAIL_FROM`
  - `DISABLE_SLA_MONITOR`, `SLA_MONITOR_INTERVAL_MS`

- Local infra defaults come from `infra/docker-compose.yml`.

## Major Routers (Core API)

- `tasks`, `certificate_acceptance`, `pons_geofence`, `photos_validate`, `assets`, `reports`, `rate_cards`, `pay_sheets`, `contracts`, `assignments`, `photos_upload_hook`, `devices`, `incidents`, `optical` (OTDR/LSPM), `closures`, `trays`, `splices`, `tests_plans`, `work_queue`, `topology`, `maintenance`, `configs`, `spares`
- Health: `GET /healthz`, `GET /readyz`

## Notes on Migration

- The project is in a transition phase towards the FastAPI + Postgres core. The Express + MongoDB API remains for compatibility and selected workflows (including existing CRA proxy and SLA email monitor). New domain modules are implemented in the FastAPI service.

## Building & Deployment

- Frontend production build: `cd client && npm run build` (can be served by Express in production or a CDN)
- Core API: deploy `uvicorn app.main:app` behind your preferred ASGI server/reverse proxy
- Database migrations: `alembic upgrade head`
- Object storage: use an S3-compatible provider; configure via env
- Email delivery: configure SMTP provider (Mailhog for local)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your edits
4. Test thoroughly
5. Submit a pull request

## License

MIT License — see `LICENSE` for details

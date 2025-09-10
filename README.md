# Fiber PON Tracker

Monorepo: FastAPI backend + React (Vite) frontend.

## Quick Start

1. Copy env
```bash
cp .env.example .env
```
2. Start DB and S3 (docker)
```bash
docker compose up -d
```
3. Install deps
```bash
cd api && pip install -r requirements.txt
cd ../web && npm i
```
4. Migrate and seed
```bash
make migrate
make seed
```
5. Run dev servers
```bash
make dev
```

## Default logins
- ADMIN: admin@example.com / Passw0rd!
- PM: pm@example.com / Passw0rd!
- SITE: site@example.com / Passw0rd!
- SMME: smme@example.com / Passw0rd!
- AUDITOR: auditor@example.com / Passw0rd!


PY=python3
PIP=pip3

.PHONY: db dev api web migrate seed fmt test

db:
	docker compose up -d db s3

stop:
	docker compose down

api-install:
	cd api && $(PIP) install -r requirements.txt

web-install:
	cd web && npm install

migrate:
	cd api && alembic -c db/alembic.ini upgrade head

seed:
	cd api && $(PY) db/seed.py

dev:
	( cd api && ENV_FILE=../.env uvicorn main:app --reload --host 0.0.0.0 --port 8000 ) & \
	( cd web && npm run dev -- --host )

api:
	cd api && ENV_FILE=../.env uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm run dev -- --host

test:
	cd api && pytest -q


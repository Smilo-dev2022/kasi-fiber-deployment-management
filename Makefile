SHELL := /usr/bin/bash
.PHONY: dev db migrate seed api web

ENV_FILE ?= .env

help:
	@echo "Targets: db, migrate, dev, seed, api, web"

db:
	docker compose up -d db

migrate:
	cd api && alembic upgrade head

seed:
	cd api && python -m db.seed

api:
	cd api && uvicorn main:app --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm run dev -- --host 0.0.0.0 --port 5173

dev:
	concurrently "make api" "make web"

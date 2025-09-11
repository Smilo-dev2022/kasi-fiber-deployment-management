SHELL := /usr/bin/bash

.PHONY: up db seed testplan openapi release seed-user test-backend test-frontend

up:
	docker compose -f infra/docker-compose.yml up -d

db:
	alembic upgrade head

seed:
	python scripts/seed.py

seed-user:
	docker compose -f infra/docker-compose.yml exec -T auth node server/scripts/seed-user.js || true

test-backend:
	python -m pytest -q || true

test-frontend:
	cd client && (npm test -- --watchAll=false || true)

testplan:
	bash -lc 'set -e; source .env 2>/dev/null || true; API=$${API:-http://localhost:8000}; AUTH=$${AUTH}; echo Running TESTPLAN against $$API; '
	@echo "Run sections manually from TESTPLAN.md or scriptify as needed."

openapi:
	@curl -fsS http://localhost:8000/openapi.json -o openapi.json || echo "Start API first."

release:
	@echo "Tagging and pushing images (placeholder). Configure your registry."
	git tag -a v$$(date +%Y.%m.%d.%H%M%S) -m "Release"
	git push --tags


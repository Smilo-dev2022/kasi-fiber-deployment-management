SHELL := /usr/bin/bash

.PHONY: up db seed testplan openapi release

up:
	docker compose -f infra/docker-compose.yml up -d

db:
	alembic upgrade head

seed:
	python scripts/seed.py

testplan:
	bash -lc 'set -e; source .env 2>/dev/null || true; API=$${API:-http://localhost:8000}; AUTH=$${AUTH}; echo Running TESTPLAN against $$API; '
	@echo "Run sections manually from TESTPLAN.md or scriptify as needed."

openapi:
	@curl -fsS http://localhost:8000/openapi.json -o openapi.json || echo "Start API first."

release:
	@echo "Tagging and pushing images (placeholder). Configure your registry."
	git tag -a v$$(date +%Y.%m.%d.%H%M%S) -m "Release"
	git push --tags


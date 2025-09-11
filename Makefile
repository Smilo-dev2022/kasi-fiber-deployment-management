.PHONY: up db seed testplan openapi release

COMPOSE=docker compose -f infra/docker-compose.yml
API?=http://localhost:8000

up:
	$(COMPOSE) up -d db redis minio mailhog api
	@echo "Waiting for API /readyz..."
	@until curl -fsS $(API)/readyz >/dev/null 2>&1; do sleep 2; done; echo OK

db:
	@echo "Running Alembic migrations"
	alembic upgrade head

seed:
	@echo "Seeding pilot data"
	python scripts/seed.py

testplan:
	@echo "Running smoke and test plan snippets (manual steps in TESTPLAN.md)"
	BASE_URL=$(API) ./scripts/smoke.sh

openapi:
	@echo "Exporting OpenAPI to openapi.json"
	python -c "from fastapi.openapi.utils import get_openapi; from app.main import app; import json; open('openapi.json','w').write(json.dumps(get_openapi(title=getattr(app,'title','API') or 'API', version='1.0.0', routes=app.routes), indent=2))" && echo "Wrote openapi.json"

release:
	@echo "Tag and push images via CI (placeholder)"
	@git tag -f release-$(shell date +%Y%m%d%H%M%S) && git push --force --tags


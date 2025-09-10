Run
1) python -m venv .venv && source .venv/bin/activate
2) pip install -r requirements.txt
3) cp .env.example .env
4) createdb fiber
5) alembic upgrade head
6) uvicorn app.main:app --reload

Default roles: ADMIN, PM, SITE, SMME, AUDITOR

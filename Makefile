run:
	npm run server

dev:
	npm run dev

seed:
	node scripts/seed.js

compose-up:
	docker compose up -d

compose-down:
	docker compose down -v

bucket:
	mc alias set local http://localhost:9000 minio minio123 || true
	mc mb --ignore-existing local/fiber-photos || true

dbdump:
	mkdir -p backups
	mongodump --uri="$$MONGODB_URI" --archive=backups/backup-`date +%Y%m%d%H%M%S`.gz --gzip || mongodump --archive=backups/backup-`date +%Y%m%d%H%M%S`.gz --gzip
	@echo "Backup written to backups/; implement retention: keep 7 daily, 4 weekly, 3 monthly"


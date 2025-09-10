run:
	npm start

dev:
	npm run dev

install:
	npm install && cd client && npm install

seed:
	node scripts/seed.js

dbdump:
	mongodump --uri=$$MONGODB_URI --archive=backup.archive

up:
	docker compose up -d

miniobucket:
	mc alias set local http://localhost:9000 minio minio123 && mc mb --ignore-existing local/$$S3_BUCKET


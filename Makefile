.PHONY: build up down stop logs processor-logs shell test lint db-init

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

stop:
	docker compose stop

logs:
	docker compose logs -f api

processor-logs:
	docker compose logs -f processor

shell:
	docker compose run --rm --entrypoint sh api

test:
	docker compose exec api pytest

lint:
	docker compose exec api ruff check src tests

db-init:
	docker compose run --rm --entrypoint python api scripts/init_db.py

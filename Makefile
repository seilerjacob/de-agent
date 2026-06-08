.PHONY: run build clean test test-unit test-e2e

run:
	docker compose up

build:
	docker compose build --no-cache

clean:
	docker compose down -v

test:
	.venv/bin/pytest tests/ -v

test-unit:
	.venv/bin/pytest tests/unit/ -v

test-e2e:
	.venv/bin/pytest tests/e2e/ -v -s

bootstrap:
	bash scripts/bootstrap.sh

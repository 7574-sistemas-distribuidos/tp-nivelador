SHELL := /bin/bash
PWD := $(shell pwd)

up:
	mkdir -p output
	COMPOSE_HTTP_TIMEOUT=300 docker compose -f docker-compose.yaml up --build --remove-orphans --detach
	docker compose -f docker-compose.yaml logs --follow
.PHONY: up

down:
	docker compose -f docker-compose.yaml stop -t 5
	docker compose -f docker-compose.yaml down
.PHONY: down

logs:
	docker compose -f docker-compose.yaml logs
.PHONY: logs

test:
	mkdir -p output
	#rm ./output/* -f
	COMPOSE_HTTP_TIMEOUT=300 docker compose -f docker-compose.yaml up --build --remove-orphans --detach
	PYTHONPATH="$(PWD)/services/server/src_frozen" python3 ./verify_output.py; EXIT_CODE=$$?; \
	docker compose -f docker-compose.yaml stop -t 5; \
	docker compose -f docker-compose.yaml down -v; \
	exit $$EXIT_CODE
.PHONY: test

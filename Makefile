SHELL := /bin/bash
PWD := $(shell pwd)
DOCKER_FILE_PATH ?= docker-compose.yaml

up:
	mkdir -p output
	rm ./output/* -f
	COMPOSE_HTTP_TIMEOUT=300 docker compose -f $(DOCKER_FILE_PATH) up --build --remove-orphans --detach
.PHONY: up

down:
	docker compose -f $(DOCKER_FILE_PATH) stop -t 5
	docker compose -f $(DOCKER_FILE_PATH) down
.PHONY: down

logs:
	docker compose -f $(DOCKER_FILE_PATH) logs --follow
.PHONY: logs

test:
	rm failed_test.log -f
	PYTHONPATH="$(PWD)" python3 tests/run.py
.PHONY: test

SHELL := /bin/bash
PWD := $(shell pwd)
DOCKER_FILE_PATH ?= docker-compose.yaml
AMOUNT_OF_CLIENTS ?= 6


up:
	mkdir -p output
	rm -f ./output/*
	COMPOSE_HTTP_TIMEOUT=300 docker compose -f $(DOCKER_FILE_PATH) up --build --remove-orphans --detach
.PHONY: up

clients:
	python3 scripts/multiple_clients_builder.py $(AMOUNT_OF_CLIENTS) $(DOCKER_FILE_PATH)
.PHONY: clients

down:
	docker compose -f $(DOCKER_FILE_PATH) stop -t 5
	docker compose -f $(DOCKER_FILE_PATH) down
.PHONY: down

logs:
	docker compose -f $(DOCKER_FILE_PATH) logs --follow
.PHONY: logs

verify:
	./scripts/echo_server_verifier.sh
.PHONY: verify

test:
	rm -f failed_test.log
	PYTHONPATH="$(PWD)" python3 tests/run.py
.PHONY: test

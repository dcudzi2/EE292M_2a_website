# Every command for this project runs through this Makefile, inside the container.
# `make` or `make help` lists the targets. Written for GNU Make 3.81+ and a POSIX sh.

.DEFAULT_GOAL := help

# Secrets and local overrides: plain KEY=value lines (see .env.example).
-include .env
export

# Name the compose project after the repository directory, lower-cased, so two
# checkouts never share containers or images. (subst/lastword copes with spaces.)
REPO_DIR := $(lastword $(subst /, ,$(subst \,/,$(CURDIR))))
export COMPOSE_PROJECT_NAME := $(shell echo "$(REPO_DIR)" | tr 'A-Z' 'a-z' | tr -c 'a-z0-9_\n-' '_')
export HOST_UID := $(shell id -u 2>/dev/null || echo 1000)
export HOST_GID := $(shell id -g 2>/dev/null || echo 1000)
APP_PORT ?= 8000
export APP_PORT

COMPOSE := docker compose -f docker/compose.yaml
RUN     := $(COMPOSE) run --rm --no-deps app
TOOLS   := $(COMPOSE) --profile tools

.PHONY: help build up down verify clean test lint fmt smoke logs shell lock

help:
	@echo "Everyday:"
	@echo "  build    build everything the project needs, into the image"
	@echo "  up       start the app at http://127.0.0.1:$(APP_PORT)"
	@echo "  down     stop the app"
	@echo "  verify   lint, test and smoke: the gate"
	@echo "  clean    return to the state of a fresh clone"
	@echo ""
	@echo "While developing:"
	@echo "  test     run the tests"
	@echo "  lint     check the code, changing nothing"
	@echo "  fmt      rewrite the code into the standard format"
	@echo "  smoke    start the app, check a real API result, stop it"
	@echo "  logs     follow the app's output"
	@echo "  shell    open a shell inside the container"
	@echo ""
	@echo "Only when dependencies change:"
	@echo "  lock     record exact versions in docker/uv.lock and docker/package-lock.json"

build:
	$(COMPOSE) build app

up:
	$(COMPOSE) up -d app
	@echo "App running at http://127.0.0.1:$(APP_PORT)"

down:
	$(COMPOSE) down

verify: build lint test smoke
	@echo "verify: all checks passed"

clean:
	$(TOOLS) down --rmi local --volumes --remove-orphans
	find . -depth \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache \) -type d -exec rm -rf {} +

test:
	$(RUN) pytest

lint:
	$(RUN) sh -c "ruff check src tests && ruff format --check src tests"

fmt:
	$(RUN) sh -c "ruff check --fix src tests && ruff format src tests"

# Start the app, check a real result from inside the container, always stop it.
smoke:
	$(COMPOSE) up -d app
	$(COMPOSE) exec -T app python tests/smoke_check.py; status=$$?; $(COMPOSE) down; exit $$status

logs:
	$(COMPOSE) logs -f app

shell:
	$(RUN) bash

lock:
	$(TOOLS) build uv node
	$(TOOLS) run --rm uv uv lock
	$(TOOLS) run --rm node npm install --package-lock-only --ignore-scripts --no-audit --no-fund
	@echo "Locks updated: commit each manifest in docker/ together with its lock."

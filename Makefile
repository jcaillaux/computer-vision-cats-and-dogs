SHELL := /bin/bash
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

env:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements/base.txt

activate:
	@echo "Run: source $(VENV)/bin/activate"
	
clear :
	rm -rf $(VENV)

up:
	@echo "Starting Docker containers..."
	docker compose --file docker/docker-compose.yml --env-file .env up -d
down:
	@echo "Stopping Docker containers..."
	docker compose --file docker/docker-compose.yml --env-file .env down

create-tables:
	$(PYTHON) -m scripts.create_tables

drop-tables:
	$(PYTHON) -m scripts.drop_tables


SHELL := /bin/bash
PYTHON ?= python3
SERVER_DIR := server

.PHONY: install run test-unit test-integration

install:
	cd $(SERVER_DIR) && $(PYTHON) -m pip install -r requirements.txt

run:
	cd $(SERVER_DIR) && $(PYTHON) -m uvicorn app:app --reload --port 1854

test-unit:
	cd $(SERVER_DIR) && $(PYTHON) -m pytest tests/unit

test-integration:
	cd $(SERVER_DIR) && $(PYTHON) -m pytest tests/integration

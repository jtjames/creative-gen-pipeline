SHELL := /bin/bash
PYTHON ?= python3
SERVER_DIR := server

.PHONY: install run test-integration

install:
	cd $(SERVER_DIR) && $(PYTHON) -m pip install -r requirements.txt

run:
	cd $(SERVER_DIR) && $(PYTHON) -m uvicorn app:app --reload --port 1854

test-integration:
	cd $(SERVER_DIR) && $(PYTHON) -m pytest tests_integration/test_dropbox_connection.py

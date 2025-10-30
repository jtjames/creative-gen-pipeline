SHELL := /bin/bash
PYTHON ?= python3
SERVER_DIR := server

.PHONY: install run test-unit test-integration test-integration-dropbox test-integration-gemini test-integration-e2e

install:
	cd $(SERVER_DIR) && $(PYTHON) -m pip install -r requirements.txt

run:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m uvicorn src.app:app --reload --port 1854

test-unit:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m pytest tests/unit

test-integration:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m pytest tests/integration

test-integration-dropbox:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m pytest tests/integration/test_dropbox_connection.py

test-integration-gemini:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m pytest tests/integration/test_gemini_connection.py

test-integration-e2e:
	cd $(SERVER_DIR) && PYTHONPATH=$(SERVER_DIR) $(PYTHON) -m pytest tests/integration/test_gemini_to_dropbox.py

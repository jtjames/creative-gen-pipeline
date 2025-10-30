"""Smoke tests for basic FastAPI routes."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

from fastapi.testclient import TestClient

SERVER_ROOT = Path(__file__).resolve().parents[2]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

warnings.filterwarnings("ignore", category=DeprecationWarning, module="dropbox.session")

from src.app import create_app  # noqa: E402  pylint: disable=wrong-import-position


class _DummyStorage:
    def generate_temporary_link(self, path: str) -> str:  # pragma: no cover - trivial helper
        return f"https://example.com/{path}"


def test_root_endpoint_returns_greeting():
    app = create_app(storage_factory=lambda _settings: _DummyStorage())
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Creative Automation API says hello!"}


def test_temporary_link_endpoint_uses_storage():
    app = create_app(storage_factory=lambda _settings: _DummyStorage())
    client = TestClient(app)

    response = client.get("/storage/temporary-link", params={"path": "demo.png"})
    assert response.status_code == 200
    assert response.json()["link"].endswith("demo.png")

"""Integration tests for the Dropbox storage helper.

These tests make real network calls. They fail fast when required
configuration is missing.
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[2]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from storage import DropboxStorage  # noqa: E402  pylint: disable=wrong-import-position
from tests.utils import load_env_from_file  # noqa: E402  pylint: disable=wrong-import-position

env_values = load_env_from_file(SERVER_ROOT / ".env")

DROPBOX_TOKEN_ENV = "DROPBOX_ACCESS_TOKEN"


def test_dropbox_upload_and_temporary_link():
    if not env_values.get(DROPBOX_TOKEN_ENV):
        raise AssertionError(
            "DROPBOX_ACCESS_TOKEN is not set. Provide it via environment or .env before running integration tests."
        )

    storage = DropboxStorage()

    storage.ensure_folder("smoke-tests")

    test_suffix = uuid.uuid4().hex
    relative_path = f"smoke-tests/integration-{test_suffix}.txt"
    artifact = storage.upload_bytes(
        path=relative_path,
        data=b"creative automation integration test",
    )
    assert artifact.path.endswith(relative_path)

    link = storage.generate_temporary_link(relative_path)
    assert link.startswith("http"), "Expected Dropbox temporary link"

    storage.delete_path(relative_path)

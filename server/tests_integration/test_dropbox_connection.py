"""Integration tests for the Dropbox storage helper.

These tests make real network calls. They are skipped automatically when the
required Dropbox access token is not available.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_env_from_file() -> None:
    """Populate os.environ with key/value pairs from .env if present."""
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


_load_env_from_file()

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    from storage import DropboxStorage  # noqa: E402  pylint: disable=wrong-import-position

DROPBOX_TOKEN_ENV = "DROPBOX_ACCESS_TOKEN"


@pytest.mark.skipif(
    not os.environ.get(DROPBOX_TOKEN_ENV),
    reason="Dropbox integration tests require DROPBOX_ACCESS_TOKEN to be set",
)
def test_dropbox_upload_and_temporary_link():
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

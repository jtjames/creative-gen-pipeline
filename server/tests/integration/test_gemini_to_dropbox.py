"""End-to-end integration test: Gemini image → Dropbox upload."""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import requests

from src.config import Settings
from src.gemini import GeminiClient
from src.storage import DropboxStorage
from tests.utils import load_env_from_file  # noqa: E402  pylint: disable=wrong-import-position

SERVER_ROOT = Path(__file__).resolve().parents[2]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))


async def _generate_image(client: GeminiClient, model: str) -> bytes:
    artifact = await client.generate_image(
        prompt="Generate a simple flat icon of a camera with a gradient background",
        mime_type="image/png",
        model=model,
    )
    if not artifact.image_bytes:
        raise AssertionError("Gemini returned empty image payload")
    return artifact.image_bytes


def _upload_and_verify(storage: DropboxStorage, folder: str, filename: str, data: bytes) -> str:
    storage.ensure_folder(folder)
    path = f"{folder}/{filename}"
    storage.upload_image(path=path, data=data)
    link = storage.generate_temporary_link(path)
    response = requests.get(link, timeout=20)
    if response.status_code != 200:
        raise AssertionError(f"Dropbox temporary link inaccessible (status {response.status_code})")
    if "image" not in response.headers.get("Content-Type", ""):
        raise AssertionError("Dropbox temporary link did not return image content")
    return path


def test_gemini_image_persisted_to_dropbox():
    env_values = load_env_from_file(SERVER_ROOT / ".env")
    gemini_key = env_values.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    dropbox_token = env_values.get("DROPBOX_ACCESS_TOKEN") or os.environ.get("DROPBOX_ACCESS_TOKEN")

    if not gemini_key:
        raise AssertionError("GEMINI_API_KEY is not set. Provide it before running the end-to-end test.")
    if not dropbox_token:
        raise AssertionError("DROPBOX_ACCESS_TOKEN is not set. Provide it before running the end-to-end test.")

    settings = Settings()
    gemini_client = GeminiClient(settings=settings)
    storage = DropboxStorage(settings=settings)

    image_model = "models/gemini-2.0-flash-preview-image-generation"

    image_bytes = asyncio.run(_generate_image(gemini_client, image_model))

    folder = "gemini-smoke"
    filename = f"{uuid.uuid4().hex}.png"
    destination_path: str | None = None
    try:
        destination_path = _upload_and_verify(storage, folder, filename, image_bytes)
    finally:
        if destination_path:
            storage.delete_path(destination_path)

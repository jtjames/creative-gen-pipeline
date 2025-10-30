"""Integration smoke test for Google Gemini API.

Requires a valid API key in the GEMINI_API_KEY environment variable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

SERVER_ROOT = Path(__file__).resolve().parents[2]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from tests.utils import load_env_from_file  # noqa: E402  pylint: disable=wrong-import-position

env_values = load_env_from_file(SERVER_ROOT / ".env")

GEMINI_API_KEY = env_values.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
DEFAULT_MODEL = "models/gemini-2.5-flash"
GEMINI_MODEL = env_values.get("GEMINI_MODEL") or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:generateContent"


def test_gemini_generate_content_smoke():
    if not GEMINI_API_KEY:
        raise AssertionError(
            "GEMINI_API_KEY is not set. Provide a valid key via environment or .env before running integration tests."
        )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "Provide one short slogan for a creative automation demo."
                    }
                ],
            }
        ],
    }

    response = requests.post(
        ENDPOINT,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=20,
    )
    if response.status_code == 404:
        raise AssertionError(
            "Gemini API returned 404. Ensure the configured model is enabled for this key or set GEMINI_MODEL to an accessible model."
        )

    response.raise_for_status()
    data = response.json()

    assert "candidates" in data and data["candidates"], "Expected candidates in Gemini response"
    first_candidate = data["candidates"][0]
    parts = first_candidate.get("content", {}).get("parts", [])
    assert parts, "Expected content parts in Gemini candidate"
    assert any("text" in part for part in parts), "Gemini candidate should include text output"

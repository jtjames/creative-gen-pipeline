"""Google Gemini API integration helpers."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from .config import Settings, get_settings

DEFAULT_GEMINI_MODEL = "models/gemini-2.5-flash"


@dataclass(frozen=True)
class GeminiImageArtifact:
    model: str
    response_id: str
    mime_type: str
    image_bytes: bytes
    raw_response: Mapping[str, Any]


class GeminiClient:
    """Thin client for interacting with the Google Gemini image generation API."""

    def __init__(self, settings: Settings | None = None, *, timeout_seconds: float = 60.0):
        self._settings = settings or get_settings()
        if not self._settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        self._timeout = timeout_seconds

    @property
    def api_key(self) -> str:
        return self._settings.gemini_api_key  # type: ignore[attr-defined]

    def _endpoint_for(self, model: str) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"

    async def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        aspect_ratio: str | None = None,
        mime_type: str = "image/png",
        model: str | None = None,
    ) -> GeminiImageArtifact:
        target_model = model or DEFAULT_GEMINI_MODEL

        contents: list[dict[str, Any]] = [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
        if negative_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"Negative prompt: {negative_prompt}"}],
            })

        generation_config: dict[str, Any] = {"responseMimeType": mime_type}
        if aspect_ratio:
            generation_config["aspectRatio"] = aspect_ratio

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._endpoint_for(target_model),
                params={"key": self.api_key},
                json=payload,
            )
        response.raise_for_status()
        data = response.json()

        candidate = _first_candidate(data)
        blob = _first_image_blob(candidate)
        image_bytes = base64.b64decode(blob)
        response_id = data.get("responseId") or candidate.get("responseId") or "unknown"

        return GeminiImageArtifact(
            model=target_model,
            response_id=response_id,
            mime_type=mime_type,
            image_bytes=image_bytes,
            raw_response=data,
        )


def _first_candidate(data: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = data.get("candidates")
    if not candidates:
        raise RuntimeError("Gemini response contained no candidates")
    return candidates[0]


def _first_image_blob(candidate: Mapping[str, Any]) -> str:
    content = candidate.get("content") or {}
    parts = content.get("parts") or []
    for part in parts:
        if blob := part.get("inlineData", {}).get("data"):
            return blob
    raise RuntimeError("Gemini candidate did not include inline image data")

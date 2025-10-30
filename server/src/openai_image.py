"""OpenAI image generation helpers."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from .config import Settings, get_settings

DEFAULT_OPENAI_IMAGE_MODEL = "dall-e-3"
_DEFAULT_MIME_TYPE = "image/png"

_ASPECT_RATIO_TO_SIZE: dict[str, str] = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
}


@dataclass(frozen=True)
class OpenAIImageArtifact:
    """Container for an OpenAI generated image."""

    model: str
    mime_type: str
    image_bytes: bytes
    prompt: str
    raw_response: Mapping[str, Any]


class OpenAIImageClient:
    """Thin async client for the OpenAI Images API."""

    def __init__(self, settings: Settings | None = None, *, timeout_seconds: float = 60.0):
        self._settings = settings or get_settings()
        if not self._settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        self._timeout = timeout_seconds

    @property
    def api_key(self) -> str:
        return self._settings.openai_api_key  # type: ignore[attr-defined]

    def _resolve_size(self, aspect_ratio: str | None, fallback: str | None) -> str:
        if fallback:
            return fallback
        if aspect_ratio and aspect_ratio in _ASPECT_RATIO_TO_SIZE:
            return _ASPECT_RATIO_TO_SIZE[aspect_ratio]
        return _ASPECT_RATIO_TO_SIZE["1:1"]

    async def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        aspect_ratio: str | None = None,
        size: str | None = None,
        model: str | None = None,
        mime_type: str = _DEFAULT_MIME_TYPE,
    ) -> OpenAIImageArtifact:
        target_model = model or DEFAULT_OPENAI_IMAGE_MODEL
        prompt_text = prompt
        if negative_prompt:
            prompt_text = f"{prompt}\n\nNegative prompt: {negative_prompt}"

        payload = {
            "model": target_model,
            "prompt": prompt_text,
            "n": 1,
            "response_format": "b64_json",
            "size": self._resolve_size(aspect_ratio, size),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", error_detail)
            except Exception:
                pass
            raise RuntimeError(
                f"OpenAI API error ({response.status_code}): {error_detail}"
            )

        data = response.json()

        try:
            first = data["data"][0]
            blob = first["b64_json"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            raise RuntimeError("OpenAI image response did not include image data") from exc

        image_bytes = base64.b64decode(blob)
        resolved_mime = first.get("mime_type", mime_type)

        return OpenAIImageArtifact(
            model=target_model,
            mime_type=resolved_mime,
            image_bytes=image_bytes,
            prompt=prompt_text,
            raw_response=data,
        )

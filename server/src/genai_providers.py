"""GenAI provider selection helpers."""

from __future__ import annotations

from typing import Union

from .config import Settings, get_settings
from .gemini import GeminiClient
from .openai_image import OpenAIImageClient

GenAIClient = Union[GeminiClient, OpenAIImageClient]


def _normalize_provider_name(provider: str | None) -> str:
    if not provider:
        raise ValueError("GenAI provider is not configured.")
    return provider.strip().lower()


def select_genai_client(settings: Settings | None = None) -> GenAIClient:
    """Instantiate the configured GenAI client."""

    settings = settings or get_settings()
    provider = _normalize_provider_name(settings.genai_provider)

    if provider == "gemini":
        return GeminiClient(settings)
    if provider == "openai":
        return OpenAIImageClient(settings)

    raise ValueError(
        "Unsupported GenAI provider: "
        f"{provider}. Supported providers: gemini, openai"
    )


def current_genai_provider(settings: Settings | None = None) -> str:
    """Return the normalized provider name from settings."""

    settings = settings or get_settings()
    return _normalize_provider_name(settings.genai_provider)


def has_genai_provider_credentials(
    provider: str, settings: Settings | None = None
) -> bool:
    """Check whether credentials exist for the given provider."""

    settings = settings or get_settings()
    provider_name = _normalize_provider_name(provider)

    if provider_name == "gemini":
        return bool(settings.gemini_api_key)
    if provider_name == "openai":
        return bool(settings.openai_api_key)

    return False

"""Integration tests for the GenAI provider helpers."""

import pytest

from src.config import Settings
from src.genai_providers import (
    current_genai_provider,
    has_genai_provider_credentials,
    select_genai_client,
)
from src.gemini import GeminiClient
from src.openai_image import OpenAIImageClient


def test_select_gemini_client():
    """Ensure the Gemini helper returns a Gemini client."""

    client = select_genai_client(
        Settings(genai_provider="gemini", gemini_api_key="test-key")
    )

    assert isinstance(client, GeminiClient)


def test_select_openai_client():
    """Ensure the OpenAI helper returns an OpenAI image client."""

    client = select_genai_client(
        Settings(genai_provider="openai", openai_api_key="test-key")
    )

    assert isinstance(client, OpenAIImageClient)


def test_unsupported_provider():
    """Unsupported providers should surface a ValueError."""

    with pytest.raises(ValueError, match="Unsupported GenAI provider"):
        select_genai_client(Settings(genai_provider="unsupported"))


def test_current_provider_name():
    """Provider lookup normalizes case."""

    settings = Settings(genai_provider="OpenAI")

    assert current_genai_provider(settings) == "openai"


def test_has_gemini_credentials():
    """Gemini is available when a key exists."""

    assert (
        has_genai_provider_credentials("gemini", Settings(gemini_api_key="test-key"))
        is True
    )


def test_has_openai_credentials():
    """OpenAI is available when a key exists."""

    assert (
        has_genai_provider_credentials("openai", Settings(openai_api_key="test-key"))
        is True
    )


def test_provider_unavailable_when_keys_missing():
    """Providers without credentials should return False."""

    empty = Settings(gemini_api_key="", openai_api_key="")

    assert has_genai_provider_credentials("gemini", empty) is False
    assert has_genai_provider_credentials("openai", empty) is False

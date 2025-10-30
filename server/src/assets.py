"""Shared helpers for creative asset management."""

from __future__ import annotations

_PLACEHOLDER_TOKENS = {
    "placeholder",
    "pending",
    "pending-generation",
}


def needs_generation(path: str | None) -> bool:
    """Return True when the stored path signals an asset still needs generation."""

    if path is None:
        return True

    normalized = path.strip().lower()
    if not normalized:
        return True

    return any(token in normalized for token in _PLACEHOLDER_TOKENS)


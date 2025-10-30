"""Test utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


def read_env(env_file: Path | None = None) -> Mapping[str, str]:
    """Return key/value pairs from a .env file without mutating os.environ."""
    path = env_file or Path(__file__).resolve().parents[1] / ".env"
    if not path.exists():
        return {}
    pairs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        pairs.setdefault(key, value)
    return pairs


def load_env_from_file(env_file: Path | None = None) -> Mapping[str, str]:
    """Load a .env file, populate os.environ, and return the mapping."""
    pairs = read_env(env_file)
    for key, value in pairs.items():
        os.environ.setdefault(key, value)
    return pairs

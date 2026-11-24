"""Loads config.yaml once so every part of the agent reads the same settings."""
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


@lru_cache
def load_config(path: str | None = None) -> dict:
    config_path = Path(path) if path else ROOT / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve(relative: str) -> Path:
    """Turn a path from config.yaml into an absolute path inside the project."""
    p = Path(relative)
    return p if p.is_absolute() else ROOT / p

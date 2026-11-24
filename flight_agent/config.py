"""Loads config.yaml once so every part of the agent reads the same settings."""
import os
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


# The agent always calls Anthropic's public API. We set this explicitly because some hosts
# (like Claude Code cloud sessions) set ANTHROPIC_BASE_URL for their own use.
API_BASE_URL = "https://api.anthropic.com"
KEY_NAMES = ("FLIGHT_AGENT_API_KEY", "ANTHROPIC_API_KEY")


def api_key() -> str | None:
    """The Anthropic API key from the environment. FLIGHT_AGENT_API_KEY is checked first
    because Claude Code cloud sessions reserve ANTHROPIC_* names for themselves."""
    for name in KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    return _key_from_env_file()


def _key_from_env_file() -> str | None:
    """Fallback: read the key from a .env file in the project folder (git ignores .env).
    Lines look like FLIGHT_AGENT_API_KEY=sk-ant-..."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if name.strip() in KEY_NAMES and value and value != "your-key-here":
            return value
    return None

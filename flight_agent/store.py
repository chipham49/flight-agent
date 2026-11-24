"""Small JSON-file stores: the search cache and the user's saved preferences (memory).

JSON files keep this beginner-friendly. In production you would swap these for
Redis (cache) and a database (preferences) without changing the rest of the agent.
"""
import json
import time

from .config import load_config, resolve
from .state import Preferences


def _read(path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write(path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# ---------- Cache: skip a repeat search for the same trip within the TTL ----------

def cache_get(key: str, max_age_minutes: float | None = None):
    """Return a saved search for this trip if it is newer than the TTL (or max_age_minutes)."""
    cfg = load_config()["cache"]
    if not cfg["enabled"]:
        return None
    entry = _read(resolve(cfg["path"])).get(key)
    max_age = (max_age_minutes or cfg["ttl_minutes"]) * 60
    if entry and time.time() - entry["saved_at"] < max_age:
        return entry
    return None


def cache_put(key: str, value: dict):
    cfg = load_config()["cache"]
    if not cfg["enabled"]:
        return
    path = resolve(cfg["path"])
    data = _read(path)
    data[key] = {**value, "saved_at": time.time()}
    _write(path, data)


# ---------- Memory: preferences remembered between runs ----------

def load_preferences() -> Preferences:
    return Preferences(**_read(resolve(load_config()["memory"]["path"])))


def save_preferences(prefs: Preferences):
    _write(resolve(load_config()["memory"]["path"]), prefs.model_dump())


# ---------- Currency: show every price in USD ----------

def to_usd(amount: float, currency: str) -> float | None:
    rates = load_config()["currency"]["rates_to_usd"]
    rate = rates.get((currency or "USD").upper())
    return round(amount * rate, 2) if rate else None

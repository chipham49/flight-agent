"""Shared test setup: a fake LLM (no API key, no cost) and temporary file locations."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flight_agent.config import load_config  # noqa: E402
from flight_agent.state import ExtractedOffer, ExtractedOffers, ParsedTrip  # noqa: E402


@pytest.fixture(autouse=True)
def temp_files(tmp_path):
    """Point cache, memory and traces at a temp folder so tests never touch real data."""
    cfg = load_config()
    saved = (cfg["cache"]["path"], cfg["memory"]["path"], cfg["traces"]["dir"])
    cfg["cache"]["path"] = str(tmp_path / "cache.json")
    cfg["memory"]["path"] = str(tmp_path / "prefs.json")
    cfg["traces"]["dir"] = str(tmp_path / "traces")
    yield tmp_path
    cfg["cache"]["path"], cfg["memory"]["path"], cfg["traces"]["dir"] = saved


def trip(**overrides) -> ParsedTrip:
    base = dict(is_flight_request=True, origin="Los Angeles", destination="New York",
                depart_date="2026-12-10", return_date=None, passengers=1, cabin="economy",
                uses_home_airport=False, missing=[])
    base.update(overrides)
    return ParsedTrip(**base)


def offer(**overrides) -> ExtractedOffer:
    base = dict(airline="Delta", price=189.0, currency="USD", origin="LAX", destination="JFK",
                depart_date="2026-12-10", depart_time="07:00", arrive_time="15:30", stops=0,
                layover_minutes=None, fare_type="main cabin",
                source_url="https://www.google.com/travel/flights/lax-jfk", source_name="Google Flights")
    base.update(overrides)
    return ExtractedOffer(**base)


class FakeLLM:
    """Stands in for the real LLM class. Returns canned answers and counts calls."""

    def __init__(self, parsed: ParsedTrip, offers: list[ExtractedOffer], urls=None, cited=None,
                 search_error: Exception | None = None):
        self.parsed, self.offers = parsed, offers
        self.urls = urls if urls is not None else ["https://www.google.com/travel/flights/lax-jfk",
                                                    "https://www.kayak.com/flights/LAX-NYC/2026-12-10"]
        self.cited = cited if cited is not None else ["Delta $189 nonstop", "Spirit $79"]
        self.search_error = search_error
        self.calls = {"parse": 0, "extract": 0, "search": 0}
        self.tracer = None

    def parse_structured(self, step, system, user, schema):
        self.calls[step] += 1
        if step == "parse":
            return self.parsed, 0.0001
        return ExtractedOffers(offers=self.offers), 0.0001

    def search_web(self, system, user):
        self.calls["search"] += 1
        if self.search_error:
            raise self.search_error
        return "Delta | $189 | LAX -> JFK | ...", self.urls, self.cited, 0.02

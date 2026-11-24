"""Data shapes shared by every step of the workflow.

AgentState is the single object passed from step to step. Each step reads it,
adds what it learned, and hands it on.
"""
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ParsedTrip(BaseModel):
    """What the parse step extracts from the user's text (filled by the LLM).

    Every field is required (nullable where it can be empty) so the schema
    works with structured outputs.
    """
    is_flight_request: bool
    origin: Optional[str] = Field(description="City or airport the trip starts from, as written; null if not given")
    destination: Optional[str] = Field(description="City or airport the trip goes to, as written; null if not given")
    depart_date: Optional[str] = Field(description="YYYY-MM-DD; null if not given")
    return_date: Optional[str] = Field(description="YYYY-MM-DD, or null for one-way")
    passengers: int
    cabin: Literal["economy", "premium_economy", "business", "first"]
    uses_home_airport: bool = Field(description="True if the user said 'from home', 'my usual airport', etc.")
    missing: list[str] = Field(description="Required details the user did not give: origin, destination, depart_date")


class ExtractedOffer(BaseModel):
    """One flight as pulled out of the search notes (filled by the LLM)."""
    airline: str
    price: float
    currency: str
    origin: str = Field(description="Airport code")
    destination: str = Field(description="Airport code")
    depart_date: str = Field(description="YYYY-MM-DD")
    depart_time: Optional[str]
    arrive_time: Optional[str]
    stops: Optional[int]
    layover_minutes: Optional[int]
    fare_type: Optional[str] = Field(description="e.g. basic economy, main cabin; null if unknown")
    source_url: str
    source_name: Optional[str]


class ExtractedOffers(BaseModel):
    offers: list[ExtractedOffer]


class TripQuery(BaseModel):
    """A validated trip, with airport codes resolved."""
    origin_codes: list[str]
    destination_codes: list[str]
    origin_label: str
    destination_label: str
    depart_date: date
    return_date: Optional[date] = None
    passengers: int = 1
    cabin: str = "economy"

    def cache_key(self) -> str:
        return "|".join([
            ",".join(self.origin_codes), ",".join(self.destination_codes),
            str(self.depart_date), str(self.return_date), str(self.passengers), self.cabin,
        ])


class FlightOffer(BaseModel):
    """One flight option found during search."""
    airline: str
    price: float
    currency: str = "USD"
    price_usd: Optional[float] = None
    origin: str
    destination: str
    depart_date: str
    depart_time: Optional[str] = None
    arrive_time: Optional[str] = None
    stops: Optional[int] = None
    layover_minutes: Optional[int] = None
    fare_type: Optional[str] = None
    source_url: str
    source_name: Optional[str] = None
    # Filled by later steps
    bag_fee_usd: Optional[float] = None
    bag_fee_source: Optional[str] = None
    true_total_usd: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    price_verified: bool = False


class Preferences(BaseModel):
    home_airport: Optional[str] = None
    max_stops: Optional[int] = None
    checked_bags: int = 0


class AgentState(BaseModel):
    user_input: str
    trace_id: str
    status: Literal["running", "needs_clarification", "refused", "no_results", "done", "error"] = "running"
    message: str = ""                       # what we tell the user at the end
    clarifying_question: Optional[str] = None
    parsed: Optional[ParsedTrip] = None
    query: Optional[TripQuery] = None
    preferences: Preferences = Field(default_factory=Preferences)
    raw_search_notes: str = ""
    searched_urls: list[str] = Field(default_factory=list)
    cited_texts: list[str] = Field(default_factory=list)
    offers: list[FlightOffer] = Field(default_factory=list)
    top_offers: list[FlightOffer] = Field(default_factory=list)
    dropped: list[str] = Field(default_factory=list)   # why offers were rejected
    from_cache: bool = False
    search_attempts: int = 0
    steps_taken: int = 0
    cost_usd: float = 0.0

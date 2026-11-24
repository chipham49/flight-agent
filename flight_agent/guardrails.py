"""Guardrails: checks on what goes IN, what comes back from the web, and what goes OUT.

Everything here is plain Python (no AI), so it is fast, free and predictable.
"""
import re
from datetime import date, timedelta
from urllib.parse import urlsplit

from .airports import same_place
from .state import FlightOffer, ParsedTrip, TripQuery

DISCLAIMER = "Prices change fast. Confirm on the source site before booking."
# Placeholder "airlines" that travel-site route pages produce when no airline is named
NO_AIRLINE = {"", "not specified", "unspecified", "unknown", "various", "multiple", "multiple airlines", "n/a", "none"}

BOOKING_WORDS = re.compile(
    # "book a flight to X" is treated as a search request; these phrases ask us to actually buy.
    r"\b(book (it|this|that|them|one of (them|these))|purchase (it|this|the|a)|buy (it|this|the ticket)|"
    r"pay for|pay (with|using|by)|(credit|debit|my) card|checkout|check out for me|reserve (it|this|that))\b",
    re.I)
PAYMENT_DATA = re.compile(r"\b(?:\d[ -]?){13,19}\b|\bcvv\b|\bcard number\b|\bpassport (number|no)\b", re.I)
INJECTION = re.compile(
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)|system prompt|you are now|"
    r"disregard (the|your) (rules|instructions)|developer mode|jailbreak", re.I)


# ---------------- Input guardrails ----------------

def check_input(text: str, max_chars: int) -> tuple[str, str] | None:
    """Return (status, message) if the input must be stopped, else None."""
    t = (text or "").strip()
    if not t:
        return "refused", "Please describe your trip, e.g. 'LAX to New York, Dec 10'."
    if len(t) > max_chars:
        return "refused", f"That request is too long. Please keep it under {max_chars} characters."
    if PAYMENT_DATA.search(t):
        return "refused", ("Please don't share card or passport numbers. I only search for prices "
                           "and never book or pay.")
    if INJECTION.search(t):
        return "refused", "I can only help find cheap flights. Please describe a trip."
    if BOOKING_WORDS.search(t):
        return "refused", ("I can search for the cheapest flights, but I can't book or pay. "
                           "Tell me the trip and I'll find options with links you can book yourself.")
    return None


def keep_stated_year(text: str, parsed: ParsedTrip) -> None:
    """If the user wrote exactly one year (e.g. "Jan 5 2020") but the model moved the date
    to another year, put the user's year back. Then validate_trip can reject a past date."""
    years = set(re.findall(r"\b(?:19|20)\d{2}\b", text))
    if len(years) != 1 or not parsed.depart_date:
        return
    year = years.pop()
    if not parsed.depart_date.startswith(year):
        parsed.depart_date = year + parsed.depart_date[4:]  # "2027-01-05" -> "2020-01-05"


def validate_trip(parsed: ParsedTrip, today: date) -> list[str]:
    """Problems with the trip details that the user must fix."""
    errors = []
    try:
        depart = date.fromisoformat(parsed.depart_date) if parsed.depart_date else None
        ret = date.fromisoformat(parsed.return_date) if parsed.return_date else None
    except ValueError:
        return ["I couldn't understand the dates. Please use a format like 'Dec 10'."]
    if depart and depart < today:
        errors.append(f"The departure date {depart} is in the past.")
    if depart and depart > today + timedelta(days=330):
        errors.append("Airlines usually sell tickets only up to about 11 months ahead.")
    if depart and ret and ret < depart:
        errors.append("The return date is before the departure date.")
    if not 1 <= parsed.passengers <= 9:
        errors.append("I can search for 1 to 9 passengers.")
    return errors


# ---------------- Web data guardrail (prompt-injection defence) ----------------

def sanitize_web_text(text: str) -> str:
    """Drop lines from web results that look like instructions to the AI."""
    return "\n".join(line for line in text.splitlines() if not INJECTION.search(line))


# ---------------- Offer validation ----------------

def _norm_url(url: str) -> str:
    p = urlsplit(url.strip())
    return f"{p.netloc.lower().removeprefix('www.')}{p.path.rstrip('/')}"


def url_was_seen(url: str, searched_urls: list[str]) -> bool:
    """The source link must be a page the web search actually returned (no invented links)."""
    if not url:
        return False
    target = _norm_url(url)
    return any(_norm_url(u) == target for u in searched_urls)


def _price_strings(price: float) -> list[str]:
    whole = f"{price:,.0f}"
    return [whole, whole.replace(",", ""), f"{price:,.2f}", f"{price:.2f}"]


def check_offer(offer: FlightOffer, query: TripQuery, searched_urls: list[str],
                cited_texts: list[str], max_stops: int | None) -> str | None:
    """Return a reason to DROP the offer, or None if it is valid. Also sets flags/warnings."""
    if (offer.airline or "").strip().lower() in NO_AIRLINE:  # found by eval v2 (fee-01)
        return f"${offer.price}: no airline named, so it can't be booked or get a bag fee"
    if not url_was_seen(offer.source_url, searched_urls):
        return f"{offer.airline} ${offer.price}: source link was not in the search results"
    if not 0 < offer.price < 50_000:
        return f"{offer.airline}: price {offer.price} is not realistic"
    if offer.price_usd is None:
        return f"{offer.airline}: unknown currency {offer.currency}"
    if not same_place(offer.origin, query.origin_codes):
        return f"{offer.airline}: departs from {offer.origin}, not {query.origin_label}"
    if not same_place(offer.destination, query.destination_codes):
        return f"{offer.airline}: arrives at {offer.destination}, not {query.destination_label}"
    if offer.depart_date != str(query.depart_date):
        return f"{offer.airline}: date {offer.depart_date} does not match {query.depart_date}"
    if max_stops is not None and offer.stops is not None and offer.stops > max_stops:
        return f"{offer.airline}: {offer.stops} stops is more than your limit of {max_stops}"

    cited = " ".join(cited_texts)
    offer.price_verified = any(s in cited for s in _price_strings(offer.price))
    if not offer.price_verified:
        offer.warnings.append("Price not quoted word-for-word in the source text; double-check it")
    if offer.fare_type and "from-price" in offer.fare_type.lower():
        offer.warnings.append("Lowest advertised price for this route, not confirmed for your date")
    if offer.fare_type and "basic" in offer.fare_type.lower():
        offer.warnings.append("Basic economy: no seat choice, no changes; some airlines exclude carry-on")
    if offer.layover_minutes and offer.layover_minutes < 60:  # 0 = nonstop, so no warning
        offer.warnings.append(f"Short layover ({offer.layover_minutes} min): risk of missed connection")
    if offer.layover_minutes is not None and offer.layover_minutes >= 8 * 60:
        offer.warnings.append(f"Long layover ({offer.layover_minutes // 60} h): may need a hotel")
    return None


# ---------------- Output guardrail ----------------

def check_output(message: str, offers: list[FlightOffer]) -> str:
    """Make sure the final answer always has sources and the disclaimer."""
    for o in offers:
        if o.source_url not in message:
            message += f"\nSource for {o.airline}: {o.source_url}"
    if DISCLAIMER not in message:
        message += f"\n\n{DISCLAIMER}"
    return message

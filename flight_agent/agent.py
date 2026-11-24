"""The orchestrator: runs the workflow steps in order on one shared AgentState.

    guard_input -> parse -> load_memory -> search -> enrich -> rank -> respond

Safety limits (no endless loops):
  - each step runs at most once per run, and the whole run has MAX_STEPS
  - the search step retries at most max_search_attempts times
  - the run stops after timeout_seconds
Every step is wrapped in a tracing span, so the trace shows exactly what happened.
"""
import time
from datetime import date

from . import guardrails, prompts
from .airports import lookup_airport
from .config import load_config
from .llm import LLM
from .rag.retriever import checked_bag_fee
from .state import AgentState, ExtractedOffer, ExtractedOffers, FlightOffer, ParsedTrip, TripQuery
from .store import cache_get, cache_put, load_preferences, to_usd
from .tracing import Tracer


class Context:
    """Things every step needs that are not part of the state."""

    def __init__(self, tracer: Tracer, llm: LLM, today: date, use_cache: bool):
        self.tracer, self.llm, self.today, self.use_cache = tracer, llm, today, use_cache
        self.cfg = load_config()


# ---------------------------------------------------------------- steps

def guard_input(state: AgentState, ctx: Context):
    stop = guardrails.check_input(state.user_input, ctx.cfg["limits"]["max_input_chars"])
    if stop:
        state.status, state.message = stop


def parse(state: AgentState, ctx: Context):
    parsed, cost = ctx.llm.parse_structured(
        "parse", prompts.PARSE_SYSTEM.format(today=ctx.today.isoformat()), state.user_input, ParsedTrip)
    state.cost_usd += cost
    state.parsed = parsed
    if not parsed.is_flight_request:
        state.status = "refused"
        state.message = "I can only help find cheap flights. Tell me where and when you want to fly."


def load_memory(state: AgentState, ctx: Context):
    """Long-term memory: fill gaps from saved preferences, then build the validated query."""
    prefs = load_preferences()
    state.preferences = prefs
    p = state.parsed
    ctx.tracer.tool_call("load_preferences", None, prefs.model_dump())

    origin = p.origin
    missing = list(p.missing)
    if (p.uses_home_airport or not origin) and prefs.home_airport:
        origin = prefs.home_airport
        missing = [m for m in missing if m != "origin"]
    if not origin and "origin" not in missing:
        missing.append("origin")

    if missing:
        names = {"origin": "where you're flying from", "destination": "where you're going",
                 "depart_date": "the exact departure date"}
        state.status = "needs_clarification"
        state.clarifying_question = "Could you tell me " + " and ".join(names.get(m, m) for m in missing) + "?"
        state.message = state.clarifying_question
        return

    errors = guardrails.validate_trip(p, ctx.today)
    if errors:
        state.status, state.message = "refused", " ".join(errors)
        return

    found = {}
    for label, text in (("origin", origin), ("destination", p.destination)):
        result = lookup_airport(text)
        ctx.tracer.tool_call("lookup_airport", text, result)
        if not result:
            state.status = "needs_clarification"
            state.clarifying_question = f"I don't know an airport for '{text}'. Could you give the city or 3-letter airport code?"
            state.message = state.clarifying_question
            return
        found[label] = result

    state.query = TripQuery(
        origin_codes=found["origin"][0], origin_label=found["origin"][1],
        destination_codes=found["destination"][0], destination_label=found["destination"][1],
        depart_date=date.fromisoformat(p.depart_date),
        return_date=date.fromisoformat(p.return_date) if p.return_date else None,
        passengers=p.passengers, cabin=p.cabin,
    )


def search(state: AgentState, ctx: Context):
    """Fallback chain: fresh cache -> web search -> retry with other sources -> stale cache -> honest failure."""
    q = state.query
    key = q.cache_key()
    if ctx.use_cache:
        hit = cache_get(key)
        if hit:
            state.from_cache = True
            ctx.tracer.tool_call("cache_get", key, "hit")
            _load_offers(state, ctx, hit)
            return
        ctx.tracer.tool_call("cache_get", key, "miss")

    limits = ctx.cfg["limits"]
    while state.search_attempts < limits["max_search_attempts"]:
        state.search_attempts += 1
        template = prompts.SEARCH_USER if state.search_attempts == 1 else prompts.SEARCH_USER_RETRY
        user = template.format(
            cabin=q.cabin.replace("_", " "), passengers=q.passengers,
            origin=q.origin_label, origin_codes=", ".join(q.origin_codes),
            destination=q.destination_label, destination_codes=", ".join(q.destination_codes),
            depart_date=q.depart_date,
            return_line=f"Return date: {q.return_date}" if q.return_date else "One-way trip.",
        )
        with ctx.tracer.span(f"search_attempt_{state.search_attempts}"):
            try:
                started = time.perf_counter()
                notes, urls, cited, cost = ctx.llm.search_web(prompts.SEARCH_SYSTEM, user)
                state.cost_usd += cost
                ctx.tracer.tool_call("web_search", user, {"urls": urls, "notes_chars": len(notes)},
                                     duration_ms=round((time.perf_counter() - started) * 1000, 1))
            except Exception as e:  # network/API problem -> try the next fallback
                ctx.tracer.tool_call("web_search", user, None, error=f"{type(e).__name__}: {e}")
                continue
            found = {"notes": guardrails.sanitize_web_text(notes), "urls": urls, "cited": cited}
            _load_offers(state, ctx, found)
            if state.offers:
                if ctx.use_cache:
                    cache_put(key, found)
                return

    stale = cache_get(key, max_age_minutes=24 * 60) if ctx.use_cache else None
    if stale:
        state.from_cache = True
        ctx.tracer.tool_call("cache_get_stale", key, "hit")
        _load_offers(state, ctx, stale)
        for o in state.offers:
            o.warnings.append("From an earlier search (prices may have changed)")
    if not state.offers:
        state.status = "no_results"
        state.message = ("I couldn't find reliable prices for this trip right now. "
                         "Try again later, or check Google Flights directly.")


def _load_offers(state: AgentState, ctx: Context, found: dict):
    """Turn search notes into validated FlightOffer records."""
    state.raw_search_notes = found["notes"]
    state.searched_urls = found["urls"]
    state.cited_texts = found["cited"]
    if "NO PRICES FOUND" in found["notes"].upper() and "|" not in found["notes"]:
        state.offers = []
        return
    if "extracted" not in found:  # cached results already hold the extracted records (saves a call)
        user = "Allowed URLs:\n" + "\n".join(found["urls"]) + f"\n\nNotes:\n{found['notes']}"
        extracted, cost = ctx.llm.parse_structured("extract", prompts.EXTRACT_SYSTEM, user, ExtractedOffers)
        state.cost_usd += cost
        found["extracted"] = [e.model_dump() for e in extracted.offers]

    valid = []
    for e in (ExtractedOffer(**d) for d in found["extracted"]):
        offer = FlightOffer(**e.model_dump(), price_usd=to_usd(e.price, e.currency))
        reason = guardrails.check_offer(offer, state.query, state.searched_urls, state.cited_texts,
                                        state.preferences.max_stops)
        if reason:
            state.dropped.append(reason)
        else:
            valid.append(offer)
    state.offers = valid


def enrich(state: AgentState, ctx: Context):
    """RAG: add checked-bag fees from the knowledge base to get the TRUE total price."""
    bags = state.preferences.checked_bags
    for o in state.offers:
        fee = checked_bag_fee(o.airline, bags)
        ctx.tracer.tool_call("rag_checked_bag_fee", {"airline": o.airline, "bags": bags}, fee)
        if fee is None:
            o.true_total_usd = o.price_usd
            if bags:
                o.warnings.append(f"Bag fee for {o.airline} unknown; total excludes {bags} checked bag(s)")
        else:
            o.bag_fee_usd = fee["fee_usd"]
            o.bag_fee_source = fee.get("source_url")
            o.true_total_usd = round(o.price_usd + fee["fee_usd"] * state.query.passengers, 2)


def rank(state: AgentState, ctx: Context):
    """Remove duplicates, sort by true total price, keep the top N."""
    seen, unique = set(), []
    for o in sorted(state.offers, key=lambda o: o.true_total_usd):
        k = (o.airline.lower(), o.depart_time, o.arrive_time, round(o.price_usd))
        if k not in seen:
            seen.add(k)
            unique.append(o)
    state.top_offers = unique[: ctx.cfg["limits"]["top_n"]]


def respond(state: AgentState, ctx: Context):
    q = state.query
    bags = state.preferences.checked_bags
    lines = [f"Cheapest flights: {q.origin_label} -> {q.destination_label}, {q.depart_date}"
             + (f" (return {q.return_date})" if q.return_date else " (one-way)"),
             ""]
    header = "| # | Total (USD) | Fare | Bag fee | Airline | Stops | Depart -> Arrive | Source |"
    lines += [header, "|---|---|---|---|---|---|---|---|"]
    for i, o in enumerate(state.top_offers, 1):
        bag = "-" if not bags else (f"${o.bag_fee_usd:.0f}*" if o.bag_fee_usd is not None else "?")
        stops = "?" if o.stops is None else ("nonstop" if o.stops == 0 else str(o.stops))
        times = f"{o.depart_time or '?'} -> {o.arrive_time or '?'}"
        lines.append(f"| {i} | ${o.true_total_usd:,.0f} | ${o.price_usd:,.0f} | {bag} | {o.airline} | "
                     f"{stops} | {times} | {o.source_url} |")
    warnings = [(i, w) for i, o in enumerate(state.top_offers, 1) for w in o.warnings]
    if warnings:
        lines += ["", "Warnings:"] + [f"- #{i}: {w}" for i, w in warnings]
    if bags:
        lines += ["", f"*Bag fees for {bags} checked bag(s) come from the airline knowledge base "
                      "(approximate; see the airline's baggage page)."]
    if state.from_cache:
        lines += ["", "(Results from a recent search, served from cache.)"]
    state.message = guardrails.check_output("\n".join(lines), state.top_offers)
    state.status = "done"


STEPS = [guard_input, parse, load_memory, search, enrich, rank, respond]


# ---------------------------------------------------------------- orchestrator

def run(user_input: str, today: date | None = None, use_cache: bool = True,
        llm: LLM | None = None, save_trace: bool = True) -> tuple[AgentState, dict]:
    cfg = load_config()
    tracer = Tracer(user_input, metadata={"prompt_version": cfg["prompt_version"], "models": cfg["models"]})
    ctx = Context(tracer, llm or LLM(tracer), today or date.today(), use_cache)
    if llm is not None:
        llm.tracer = tracer
    state = AgentState(user_input=user_input, trace_id=tracer.trace_id)
    deadline = time.monotonic() + cfg["limits"]["timeout_seconds"]

    for step in STEPS:
        if state.status != "running":
            break
        state.steps_taken += 1
        if state.steps_taken > cfg["limits"]["max_steps"] or time.monotonic() > deadline:
            state.status, state.message = "error", "Stopped: the search took too long. Please try again."
            break
        try:
            with tracer.span(step.__name__):
                step(state, ctx)
        except Exception as e:  # any unexpected failure ends the run safely with a clear message
            state.status = "error"
            state.message = f"Something went wrong during '{step.__name__}'. Please try again. ({type(e).__name__})"
            break

    trace = tracer.finish(state)
    if save_trace:
        tracer.save()
    return state, trace

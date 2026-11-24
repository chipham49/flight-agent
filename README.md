# ✈️ Cheapest Flight Finder Agent

An AI agent that finds the **3 cheapest flights** for a trip, adds **checked-bag fees** to show the
**true total cost**, flags risky itineraries, and links every price to its source.
It only searches. It never books or pays.

```
$ python -m flight_agent "LAX to New York on December 15"
```

## The problem

Finding a cheap flight means checking several sites, then discovering bag fees and basic-economy
restrictions late. That costs 30–60 minutes per trip, and the "cheapest" fare is often not the cheapest
once a suitcase is added.

**User:** a budget traveller who wants an answer in under a minute, with sources they can trust.

**Why an agent and not a script?** Requests are messy ("cheap flight to London next month"), the
search needs judgement across sources, and results must be checked and enriched with fee rules. Fixed
code can't read free text or search pages; an LLM can't be trusted alone with prices. The agent
combines both: **LLM for understanding and searching, plain code for validating and ranking.**

## Architecture

```
user text
   │
   ▼
1. guard_input ── refuse: booking/payment, card numbers, prompt injection, too long
   │
   ▼
2. parse ──────── Claude Haiku 5.5 + structured output → ParsedTrip (dates resolved)
   │
   ▼
3. load_memory ── saved preferences (home airport, bags, max stops) fill gaps
   │              airport tool → codes (NYC → JFK, LGA, EWR); date checks
   │              missing info → ask a clarifying question (max 2)
   ▼
4. search ─────── cache hit? → reuse
   │              Claude Sonnet 5.5 + web search (≥2 sources) → notes + URLs
   │              Haiku extracts flight records → guardrails validate each one
   │              fallback chain: retry other sources → stale cache → honest "no results"
   ▼
5. enrich (RAG) ─ airline knowledge base → bag fee → true total = fare + bags
   ▼
6. rank ───────── de-duplicate, sort by true total, keep top 3
   ▼
7. respond ────── table + warnings + sources + disclaimer (output guardrail)

Every step runs inside a tracing span → traces/<trace_id>.json
```

**One shared state object** (`AgentState` in `flight_agent/state.py`) is passed through the steps.
**No endless loops:** each step runs once, the run is capped at 12 steps and 120 seconds, search retries
at most once, web search is capped at 6 queries per call, and clarifying questions at 2.

### Design decisions

| Decision | Why |
|---|---|
| Fixed workflow, not a free-roaming agent | Predictable, testable and traceable; the LLM only does what needs judgement |
| Cheap model (Haiku) for parsing and extraction, stronger model (Sonnet) for web research | Cuts cost on the simple steps |
| Prices validated by code, not by the LLM | A price is kept only if its link came from the actual search results and the route and date match, which stops invented prices |
| RAG for bag fees | Fee rules are long, change often and differ per airline; retrieval with citations beats stuffing them into the prompt |
| Search only, never book | Safety and scope |

## How the course criteria are covered

| Criterion | Where |
|---|---|
| 1. Problem & design | This README: problem, user, architecture, decisions |
| 2. Orchestration | `flight_agent/agent.py`: 7 steps, shared `AgentState`, preferences memory, step/time/retry limits |
| 3. Tools | Claude web search, airport lookup (`airports.py`), bag-fee RAG (`rag/`), currency conversion and cache (`store.py`) |
| 4. RAG | `knowledge/*.md` + `rag/retriever.py`: section chunking, query rewriting (synonyms), airline metadata filter, BM25 ranking, citations |
| 5. Observability | `tracing.py`: per-run trace with spans, every LLM call (full prompt, response, tokens, cost), every tool call |
| 6. Evaluation | `evals/`: 15-case dataset, automatic scoring, v1 vs v2 comparison with a regression gate; `tests/`: 27 tests run in CI |
| 7. Guardrails | `guardrails.py`: input checks, web-text sanitising, offer validation, output check; refusal fallback model; fallback chain |
| 8. Performance & cost | Cost and latency measured per run; 30-minute cache; Haiku on cheap steps; prompt caching on the search prompt |
| 9. Production | Modular package, `config.yaml`, env-var secrets, `Dockerfile`, GitHub Actions CI |
| 10. Demo | See "Demo" below |

## Run it

**1. Add your API key** as an environment variable named `FLIGHT_AGENT_API_KEY`
(`ANTHROPIC_API_KEY` also works locally). Never commit it.
In a Claude Code cloud session, add it in the environment settings as `FLIGHT_AGENT_API_KEY`:
cloud sessions reserve `ANTHROPIC_*` names for Claude Code itself. Locally:

```bash
export FLIGHT_AGENT_API_KEY=your-key-here
```

**2. Install**

```bash
pip install -r requirements.txt
```

**Check the key works** (free: it only lists models, no tokens used)

```bash
python -m flight_agent --check-key
```

**3. Search**

```bash
python -m flight_agent "LAX to New York on December 15"
```

**Preferences (memory)**

```bash
python -m flight_agent --set home_airport=SFO --set checked_bags=1 --set max_stops=1
```

```bash
python -m flight_agent "from my usual airport to Seattle on December 20"
```

**Tests** (free, using a fake LLM)

```bash
python -m pytest -q
```

**Evals** (real API calls, about $1–3 per run)

```bash
python -m evals.run_evals --version v1
```

```bash
python -m evals.compare v1 v2
```

**Docker**

```bash
docker build -t flight-agent .
```

```bash
docker run -e FLIGHT_AGENT_API_KEY flight-agent "LAX to New York on December 15"
```

## Results

_Filled in after the eval runs: see `evals/results/v1.md`, `evals/results/v2.md` and `evals/results/compare_v1_v2.md`._

| Metric | v1 | v2 |
|---|---|---|
| Pass rate (15 cases) | – | – |
| Route accuracy | – | – |
| Citation rate | – | – |
| Avg cost per search | – | – |
| Median seconds per search | – | – |

**Manual check:** for 3 trips, the agent's cheapest price compared with Google Flights: _to fill in_.

## Limitations (honest list)

- Prices come from web search results, not a booking API, so some sites hide prices from search and results can be incomplete.
- Bag fees in `knowledge/` are based on published 2025 policies and are **not re-verified**. Budget airlines price bags dynamically. Always check the airline's page.
- The airport list covers about 80 major airports.
- Currency rates in `config.yaml` are fixed approximations.

## Next steps

A real flight-price API, flexible dates (±3 days), price-drop alerts, an MCP server for the tools, a web UI,
a hosted tracing tool (Langfuse), an LLM-as-judge for answer quality, and live refresh of the bag-fee knowledge base.

## Demo

A 3-minute recording that shows:
1. The problem
2. A live run with a suitcase preference
3. A trace file
4. The v1 vs v2 eval comparison
5. Next steps

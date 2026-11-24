# Project Plan: Cheapest Flight Finder Agent
*AgentOps course capstone. This plan is written to score well on the course criteria.*

---

## Part 1: What the grading criteria mean for this project

The course grades 10 areas (100 points in total). The first simple plan, a single script that calls web search, would score around **40/100**, because it has no RAG, no tracing, no memory and no deployment. This plan adds the smallest set of features that moves each area to **"Good"**, and to **"Excellent"** where that is cheap to do.

| # | Criterion | Points | Target band | What gets us there (summary) |
|---|---|---|---|---|
| 1 | Problem & System Design | 10 | Excellent (9) | Clear user problem, workflow diagram, and written reasons for every design choice |
| 2 | Agent Architecture & Orchestration | 15 | Excellent (13) | Step-by-step workflow with a shared state object, memory, and hard loop limits |
| 3 | Tooling & Integration | 10 | Excellent (9) | Flight API + web search + airport DB + currency API, served as an **MCP server** |
| 4 | Retrieval / Knowledge (RAG) | 10 | Good–Excellent (8–9) | Airline baggage and fare-rule knowledge base with query rewriting and reranking |
| 5 | Observability | 10 | Excellent (9) | Langfuse traces: one span per step, every tool call, prompt, token count and cost |
| 6 | Evaluation & Testing | 15 | Excellent (13) | 30-case dataset, automated eval script, regression gate in CI, v1 vs v2 comparison |
| 7 | Reliability & Guardrails | 10 | Excellent (9) | Input/output validation, fallback chain, prompt-injection defence, no-booking rule |
| 8 | Performance & Cost | 5 | Excellent (5) | Measured latency and cost per run, SQLite cache, cheaper model for simple steps |
| 9 | Production Readiness | 10 | Good (8) | Modular code, config files, Docker, CI, a small web UI deployed online |
| 10 | Demo & Explanation | 5 | Excellent (5) | A story-driven 5-minute demo with a live trace walkthrough |
| | **Target total** | **100** | **~88** | |

> **Beginner tip:** points are weighted. Areas 2 and 6 are worth 15 each, so spend the most care there. Area 8 is worth only 5, so do the minimum that reaches Excellent.

---

## Part 2: The design, area by area

### 1. Problem & System Design (10)

**Problem:** Finding the cheapest flight means checking many sites, comparing prices that hide fees (bags, seat selection), and spotting risky itineraries. That takes 30–60 minutes per trip.

**User:** A budget-conscious traveller who books 3–6 trips a year and wants an answer in under a minute.

**Agent's role:** a *research assistant*, not a booking bot. It understands the request, searches several sources, checks the facts, works out the **true total cost** (fare + bags), and explains its choice with sources.

**Why an agent and not a plain script?** User requests are messy ("cheap flight to London next month"), the right tools depend on the request, and results need judgement (fee rules, risky layovers). A fixed script can't handle that; an LLM with tools and rules can.

**Design decisions to write down (one paragraph each, in `docs/decisions.md`):**
1. A workflow with fixed steps rather than a free-roaming agent → predictable, testable, no loops.
2. A flight API first, with web search as fallback → structured data is more reliable than scraped pages.
3. RAG for airline fee rules → fee rules change and are too long to put in the prompt.
4. A small model for parsing and a strong model for reasoning → lower cost.
5. Search only, never booking → safety and scope.

### 2. Agent Architecture & Orchestration (15)

**Workflow (each box is one Python function, called a "node"):**

```
            ┌──────────────┐
 user ────► │ 1. Guard-in  │  reject off-topic / unsafe / invalid input
            └──────┬───────┘
                   ▼
            ┌──────────────┐  missing info? ──► ask user ──► (back to 2)
            │ 2. Parse     │  text → TripQuery (Haiku 5.5, structured output)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 3. Memory    │  load user prefs (home airport, max stops, bags)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 4. Plan      │  pick tools + sources, nearby airports (Sonnet 5.5)
            └──────┬───────┘
                   ▼
            ┌──────────────┐  cache hit? ──► skip to 6
            │ 5. Search    │  flight API → fallback web search (parallel)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 6. Enrich    │  RAG: airline bag fees & fare rules → true total
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 7. Validate  │  code checks: route, dates, price-in-source, dedupe
            │    & Rank    │
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 8. Respond + │  top 3 table, sources, warnings; save to history
            │    Guard-out │
            └──────────────┘
```

**State:** one `AgentState` object (a Pydantic model) passed between nodes. It holds the query, preferences, raw results, offers, warnings, step count, cost so far and a trace ID. Every node reads the state and returns an updated copy.

**Memory:**
- *Short-term:* the conversation history within a session, so a clarifying question and its answer stay connected.
- *Long-term:* user preferences and past searches stored in SQLite (`preferences` and `search_history` tables).

**Loop protection ("no loops" in the rubric):**
- `MAX_STEPS = 12` for the whole run
- `MAX_TOOL_CALLS = 10`
- At most 2 clarifying questions
- A 60-second total timeout
- Identical tool calls are blocked, since repeating them is a common way agents get stuck

**Framework:** plain Python with an explicit node list. Claude Code can generate it, and it's easy to read and explain. (LangGraph is an option, but it adds a concept to learn.)

### 3. Tooling & Integration (10)

| Tool | Type | Purpose |
|---|---|---|
| `search_flights_api` | External API (e.g. SerpAPI Google Flights; check today which free tier works) | Main source of structured prices |
| `web_search` | Claude's built-in web search | Fallback and cross-check from a second source |
| `lookup_airport` | Local SQLite DB (OpenFlights airports data) | City → airport codes, nearby airports |
| `convert_currency` | Free FX API (e.g. Frankfurter) | Put every price in USD |
| `search_airline_rules` | RAG retriever (see area 4) | Bag fees and fare rules |
| `get/save_preferences` | SQLite | Long-term memory |

**MCP:** package the tools as an **MCP server** using the official MCP Python SDK. The agent calls tools through MCP, and the same server also works inside Claude Desktop. That makes a nice demo moment and is the "tool ecosystem" the Excellent band asks for.

Every tool has: a typed input/output schema, a timeout, a retry policy and a clear error message.

### 4. Retrieval / Knowledge, RAG (10)

**Knowledge base:** 25–40 short Markdown documents in `knowledge/`:
- Carry-on and checked-bag fees for ~15 common airlines (budget and full-service)
- What "basic economy" excludes, per airline
- Minimum connection times for ~10 big hub airports
- General tips: self-transfer risk, airport changes, overnight layovers

Each document has a header with `airline`, `topic`, `source_url` and `collected_on`.

**Pipeline:**
1. **Chunk** the documents by section (~300 words each).
2. **Embed** them with a free local model (`sentence-transformers/all-MiniLM-L6-v2`) and store them in **Chroma**, a local vector database.
3. **Query rewrite:** Haiku rewrites the need into precise queries, e.g. "Spirit flight with a suitcase" → "Spirit Airlines checked bag fee" and "Spirit Airlines carry-on fee".
4. **Retrieve** the top 8 chunks, using metadata filters (airline name).
5. **Rerank** with a cross-encoder model (`ms-marco-MiniLM`) and keep the top 3.
6. **Multi-hop:** the flight result names the airline → retrieve that airline's fare-class rules → retrieve its bag fee for that fare class.
7. **Cite:** every fee shown links back to its `source_url` and date.

**RAG metrics** (these feed area 6): retrieval hit rate@3, citation correctness, and fee accuracy on 10 hand-written questions.

### 5. Observability (10)

**Tool:** **Langfuse** (free cloud tier, a simple Python SDK, and a good UI for screenshots).

Captured for every run:
- One **trace** per user request, tagged with user ID, prompt version, model names and git commit
- One **span** per node (Parse, Plan, Search…), with its duration
- Every **tool call**: inputs, outputs, errors, retries
- Every **LLM call**: the full prompt, response, tokens and cost
- **Scores** attached to traces from the evals (area 6)

Also: structured JSON logs to a local file as a backup, and a `trace_id` printed with every answer so a run can be found again.

### 6. Evaluation & Testing (15)

**Dataset:** `evals/dataset.jsonl` with **30 cases**:

| Group | Count | Examples |
|---|---|---|
| Normal domestic | 8 | "LAX to JFK Dec 10" |
| International | 6 | "SFO to Tokyo Jan 5–15" |
| Vague / messy | 5 | "cheap flight to london next month" |
| Fee-sensitive (RAG) | 5 | "Vegas trip with a checked bag" |
| Guardrail / adversarial | 4 | past date, "book it for me", prompt-injection text, off-topic |
| Memory | 2 | "use my usual home airport" |

**Replay mode:** record the real API and search responses once and replay them during evals, so results are repeatable and free to re-run.

**Metrics** (computed automatically):

| Metric | Type | Target |
|---|---|---|
| Parse accuracy | Code check vs expected JSON | ≥ 95% |
| Offer validity (route/dates match) | Code | 100% |
| Hallucinated prices (price not in source) | Code | 0% |
| Cheapest-in-top-3 | Code vs recorded data | ≥ 80% |
| Fee accuracy (RAG) | Code vs expected fee | ≥ 80% |
| Guardrail pass rate | Code | 100% |
| Answer quality (clarity, warnings) | LLM-as-judge with a rubric | ≥ 4/5 |
| Cost and latency per case | Code | < $0.10, < 30 s |

**Automation:**
- `python -m evals.run --version v1` writes `evals/results/v1.json` and a Markdown report.
- **Regression:** a GitHub Actions workflow runs the evals (replay mode) on every pull request and fails if any key metric drops.
- **Comparison:** `python -m evals.compare v1 v2` prints a before/after table. Use it to compare prompt v1 vs v2 and Sonnet vs Haiku for one step.
- **Unit tests** (`pytest`) for validators, the ranker and each tool's parsing.

### 7. Reliability & Guardrails (10)

**Input guardrails**
- Pydantic validation: real airport codes, future dates, return after departure, 1–9 passengers
- An off-topic or unsafe request gets a polite refusal
- Booking or payment requests get "I can only search"

**Tool and data guardrails**
- Web page text is treated as **data, not instructions** (prompt-injection defence), and has instruction-like text removed before the LLM sees it
- Timeouts and retries with backoff on every tool

**Output guardrails**
- Every price must appear in a fetched source, otherwise it's dropped
- The output must match the schema, or one repair attempt is made and then it fails safely
- A "prices change — confirm before booking" disclaimer is always included
- No personal data is stored beyond preferences the user chose to save

**Fallback chain:** flight API → web search → cached result (labelled with its age) → honest "I couldn't find reliable prices".

### 8. Performance & Cost (5)

- **Measure:** latency per node and cost per run, taken from the Langfuse data. Put a table in the README.
- **Optimise:**
  - SQLite **cache** of search results with a 30-minute TTL
  - **Prompt caching** for the long system prompt
  - **Haiku 5.5** for parse, rewrite and judge; **Sonnet 5.5** only for plan and final answer
  - **Parallel** tool calls in the Search step
- **Show the win:** report cost and latency before vs after the cache and model routing, e.g. "−60% cost".

### 9. Production Readiness (10)

```
flight-agent/
├── src/flight_agent/
│   ├── nodes/          # one file per workflow step
│   ├── tools/          # MCP server + tool implementations
│   ├── rag/            # ingest, retrieve, rerank
│   ├── guardrails/     # input/output validators
│   ├── memory/         # SQLite store
│   ├── state.py
│   ├── config.py       # reads config.yaml + environment variables
│   └── app.py          # FastAPI endpoint
├── ui/streamlit_app.py # simple web UI for the demo
├── knowledge/          # RAG documents
├── evals/
├── tests/
├── config.yaml         # models, limits, TTLs (no secrets)
├── .env.example        # names of secrets, no values
├── Dockerfile
├── .github/workflows/ci.yml
└── README.md
```

- **Config:** all models, limits and URLs live in `config.yaml`; secrets live in environment variables.
- **Deploy:** the Streamlit UI on Streamlit Community Cloud or Hugging Face Spaces (free).
- **Health check:** a `/health` endpoint, structured logs, and versioned prompts in `prompts/`.
- **Scale write-up** (half a page in `docs/production.md`): how to scale to more users (stateless API, shared cache in Redis, rate limits, cost alerts).

### 10. Demo & Explanation (5)

**5-minute story:**
1. **Hook (30 s):** "I spent 45 minutes finding a flight to Denver. Then I paid $70 in bag fees I didn't see."
2. **Live demo (2 min):** a vague request → clarifying question → top 3 with *true total cost* and a warning about a risky layover.
3. **Under the hood (1 min):** open the Langfuse trace and show the spans, tool calls and RAG retrieval.
4. **Proof (1 min):** v1 vs v2 eval comparison table, and the CI regression check on a PR.
5. **Close (30 s):** lessons learned and what's next.

Backup: a recorded video and screenshots in case live APIs fail.

---

## Part 3: TODAY — the planning checklist

Goal for today: **finish every planning document**, so building can start tomorrow with no open questions. No coding today. Times add up to about 8 hours, with breaks.

### ☐ Block 1: Setup and scope (45 min)
- [ ] Read the criteria table again and note the target score per area (copy the Part 1 table)
- [ ] Decide the deadline and the hours available per day → write them in `docs/timeline.md`
- [ ] Merge the open `add-issue-list` pull request, as GitHub practice

**Done when:** you know the deadline and the target of ~88/100.

### ☐ Block 2: Problem statement — criterion 1 (45 min)
File: `docs/01-problem.md`
- [ ] Who the user is (1 short persona)
- [ ] The problem, in 3 sentences with a real example and numbers ("45 minutes, $70 surprise fees")
- [ ] Why an agent and not a script (3 bullets)
- [ ] In scope / out of scope table
- [ ] Success metrics (link to the eval targets)

**Done when:** a classmate could explain your problem after reading it for 1 minute.

### ☐ Block 3: Architecture and decisions — criteria 1 and 2 (90 min)
Files: `docs/02-architecture.md`, `docs/decisions.md`
- [ ] Draw the workflow diagram (copy the one above, or draw it in Excalidraw and save a PNG)
- [ ] For each of the 8 nodes, write: input, output, model or code used, what can go wrong
- [ ] List the fields in `AgentState`
- [ ] Describe the memory design: what is remembered, where, and for how long
- [ ] Write down the loop limits and why you chose those numbers
- [ ] Write the 5 design decisions (1 paragraph each: decision, options, why)

**Done when:** the diagram and node table are complete.

### ☐ Block 4: Tools — criterion 3 (45 min)
File: `docs/03-tools.md`
- [ ] For each of the 6 tools: name, purpose, inputs, outputs, timeout, failure behaviour
- [ ] Sign up for the flight API and confirm the free-tier limits (write them down)
- [ ] Confirm the currency API works (open its URL in a browser)
- [ ] Download the OpenFlights airports file link and note it
- [ ] Write 3 sentences on why tools are served through MCP

**Done when:** every tool has a spec and every external account exists.

### ☐ Block 5: RAG — criterion 4 (60 min)
File: `docs/04-rag.md`
- [ ] Choose the 15 airlines and 10 hub airports to cover
- [ ] Write the document template (header fields + sections)
- [ ] Collect sources: for each airline, find the official baggage-fee page URL and paste it into a list (no writing the documents yet)
- [ ] Write down the pipeline steps (chunk → embed → rewrite → retrieve → rerank → multi-hop → cite)
- [ ] Write 10 RAG test questions with expected answers

**Done when:** the source list and the 10 questions are ready.

### ☐ Block 6: Evals — criterion 6 (75 min)
File: `docs/06-evals.md` + `evals/dataset.jsonl` (draft)
- [ ] Write all 30 test cases (input + expected behaviour) using the group table above
- [ ] Write the metrics table with targets
- [ ] Describe replay mode in 3 sentences
- [ ] Describe the regression rule ("CI fails if parse accuracy drops >2 points or hallucinations > 0")
- [ ] Plan 2 comparisons: prompt v1 vs v2, and Haiku vs Sonnet for the Parse step

**Done when:** the 30 cases are written down.

### ☐ Block 7: Observability, guardrails, cost — criteria 5, 7, 8 (60 min)
Files: `docs/05-observability.md`, `docs/07-guardrails.md`, `docs/08-cost.md`
- [ ] Create a free Langfuse account and save the keys safely, never in the repo
- [ ] List what each trace, span and tool-call record contains
- [ ] Write the guardrail list (input / tool / output) and the fallback chain
- [ ] Set a cost budget: max $ per run, max $ for the whole project; set the Anthropic Console spending limit
- [ ] List the 4 optimisations and how you'll measure before/after

**Done when:** the three files exist and the accounts are created.

### ☐ Block 8: Production and demo — criteria 9, 10 (40 min)
Files: `docs/09-production.md`, `docs/10-demo.md`
- [ ] Copy the folder structure; write which settings go in `config.yaml` vs `.env`
- [ ] Choose a deploy target (Streamlit Cloud or HF Spaces) and create the account
- [ ] Write the half-page scaling notes
- [ ] Write the 5-minute demo script with times

**Done when:** the demo script is timed and the deploy account exists.

### ☐ Block 9: Turn the plan into GitHub work (40 min)
- [ ] Ask Claude Code to replace the old issues with new ones matching this plan, one issue per build task, labelled by criterion (`c1-design` … `c10-demo`)
- [ ] Create build milestones (see Part 4)
- [ ] Commit all the planning docs on a branch, open a PR and merge it

**Done when:** the board shows every build task and the plan is on `main`.

---

## Part 4: Build phases after today (overview)

| Phase | Focus | Criteria |
|---|---|---|
| A | Project skeleton, config, state, nodes with fake tools, tests | 2, 9 |
| B | Real tools + MCP server + SQLite memory | 3, 2 |
| C | Langfuse tracing on everything | 5 |
| D | Guardrails + fallback chain | 7 |
| E | RAG knowledge base + pipeline | 4 |
| F | Eval dataset, runner, replay, CI regression | 6 |
| G | Caching, model routing, before/after numbers | 8 |
| H | UI, Docker, deploy | 9 |
| I | v2 improvements from eval failures, comparison report | 6 |
| J | Demo script, slides, backup video | 10 |

**Order tip:** do **F (evals) early**, right after B. Then every later phase can show its improvement in numbers, which is what scores 13–15 on criterion 6.

## Risks

| Risk | Plan |
|---|---|
| The flight API free tier is too small or unreliable | Replay mode for evals; web-search fallback |
| RAG fee data goes out of date | Show `collected_on` dates; present it as a known limitation |
| Too much to build | Cut order: deploy → MCP → multi-hop RAG. Keep evals and tracing at all costs (25 points) |
| API costs | Spending limit, cache, Haiku for simple steps, replay mode |

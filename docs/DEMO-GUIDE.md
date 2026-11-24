# Demo Guide (plain language)

This guide is for you, the project owner. It explains what the project does, how to start it,
what to show in your 3-minute video, and what to check before you submit. No coding needed.

---

## 1. What this project is, in one breath

You type a trip like **"LAX to New York on December 15"**. The agent:

1. **Checks your request is safe.** It refuses booking, card numbers and tricks.
2. **Understands it** using a small, cheap AI model.
3. **Uses your saved preferences** (home airport, bags, max stops). This is its *memory*.
4. **Searches the web** for real prices using a stronger AI model, then **throws away any price it can't prove**
   (wrong route, wrong date, or a link that didn't come from the search).
5. **Adds bag fees** from a small library of airline rules. This is the *RAG* part.
6. **Shows the 3 cheapest**, with links and warnings.

Every run writes a **trace file**, a full diary of what happened, how long it took and what it cost.

---

## 2. Start the app (the easy way: the web page)

You need Python installed and your API key set (see the README, "Run it").

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

A browser tab opens at **http://localhost:8501**. If it doesn't, copy that address into your browser.

What you see:

| Part of the page | What it does |
|---|---|
| **Left side: Your preferences** | Home airport, number of checked bags, max stops. Click **Save preferences**. The agent remembers them. |
| **Use cache** switch | On = a repeat search within 30 minutes is reused (fast, almost free). |
| **Example buttons** | One click fills in a trip. Includes 3 "tricky" ones (past date, booking, vague). |
| **Find cheapest flights** | Runs the agent. A fresh search takes about 30 seconds. |
| **How the agent worked** | Time, cost, each step, each tool used, each AI call. Great for the demo. |
| **Past runs (traces)** tab | Every earlier run, with time and cost. Click one to open it. |

To stop the app, go back to the terminal and press **Ctrl + C**.

> **Cost:** a fresh search costs about **$0.07–0.08**. A cached repeat or a refused request costs **under $0.001**.

---

## 3. Your 3-minute demo script

Before recording: start the app, set **Checked bags = 1** in the sidebar, click **Save preferences**,
and run **LAX → New York** once so the cache is warm (do this within 30 minutes of recording).

| Time | Show | Say (roughly) |
|---|---|---|
| **0:00–0:20** The problem | The page title | "Finding a cheap flight means checking many sites, then getting surprised by bag fees. My agent finds the 3 cheapest flights, adds bag fees for the true price, and links every price to its source. It never books or pays." |
| **0:20–1:20** Live run | Click **🌲 SFO → Seattle** (fresh, ~30 s), then **✈️ LAX → New York** (cached) | "It understood my text, used my saved preference of 1 bag, searched the web, and added the bag fee from its airline knowledge base. Every price has a source link and warnings. Running a trip again uses the cache: about 1 second and almost free, compared with 30 seconds and 7 cents." |
| | Click **📅 Past date** and **🛑 Booking request** | "Guardrails: a past date is rejected and a booking request is refused before any money is spent." |
| **1:20–2:00** Trace | Scroll to **How the agent worked**, open **Full trace file** | "Every run is traced: each step, each tool call, each AI call with its prompt, tokens, time and cost. Here's the search step: 6 web searches, the extract step, and the bag-fee lookup." |
| **2:00–2:40** Evals | Open `evals/results/compare_v1_v2.md` on GitHub | "I test it with a fixed set of cases and automatic scoring. Version 1 failed on X; I fixed it, and version 2 improved Y. 28 automatic tests run on every pull request." |
| **2:40–3:00** Next steps | README "Next steps" | "Next: a real flight-price API, flexible dates, and price alerts." |

If evals haven't been run yet, show the **Tests** instead: run `python -m pytest -q` in the terminal
(28 passed), and say the eval dataset is ready in `evals/dataset.jsonl`.

---

## 4. Where each grading point is (for your write-up)

| Criterion | Show this |
|---|---|
| 1. Problem & design | README: problem, diagram, design decisions |
| 2. Orchestration | `flight_agent/agent.py`: the 7 steps in order, one shared state, memory, step/time limits |
| 3. Tools | Web search, airport lookup, bag-fee lookup, currency table, cache: see "Tool calls" in the app |
| 4. RAG | `knowledge/` (10 airline notes + general rules) + `flight_agent/rag/`: the bag-fee column in results |
| 5. Observability | "How the agent worked" panel, `traces/examples/*.json` |
| 6. Evaluation | `evals/` (dataset, scorer, v1 vs v2 compare), `tests/` (28 tests), CI on GitHub |
| 7. Guardrails | Past date, booking, vague examples; "Offers rejected by the guardrails" list |
| 8. Cost | Time and $ on every run, cache (1 s vs 30 s), cheap model for simple steps |
| 9. Production | `config.yaml`, `.env.example`, `Dockerfile`, CI, tests, web UI |
| 10. Demo | Your video, following the script above |

Sample traces you can open on GitHub, in `traces/examples/`:

| File | What it shows |
|---|---|
| `1-fresh-search-lax-nyc.json` | A full fresh search: 27 s, $0.065 |
| `2-cache-hit-lax-nyc.json` | The same trip again from cache: 1 s, $0.0002 |
| `3-refused-past-date.json` | Past date rejected, no web search |
| `4-refused-booking.json` | Booking refused before any AI call ($0) |
| `5-asks-clarifying-question.json` | Vague request: the agent asks a question |
| `6-clarified-lax-miami-with-bag.json` | Answer added, search done, bag fee added from RAG |

---

## 5. Before you submit (checklist)

- [ ] Run the evals (costs about $0.50 for the quick set) and fill in the README "Results" table. Ask Claude Code to do it.
- [ ] Spot-check 3 prices on Google Flights and write the result in the README ("Manual check").
- [ ] Merge the pull request into `main` on GitHub.
- [ ] Make sure no API key is in the repo. It never is in the code: it only lives in the `FLIGHT_AGENT_API_KEY` setting.
- [ ] Record the video and submit the repo link + video.

## 6. If something goes wrong

| You see | Do this |
|---|---|
| "No API key" | Set `FLIGHT_AGENT_API_KEY` (see README), then restart the app |
| `streamlit: command not found` | Run `pip install -r requirements.txt` again |
| "No reliable prices found" | Normal for some routes: web search can't see every site. Try another trip or try again later |
| A search takes long | Fresh searches take 20–50 seconds. The limit is 2 minutes, then it stops safely |

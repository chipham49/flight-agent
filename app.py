"""Simple web UI for the flight agent (a demo prototype).

Run it with:   streamlit run app.py
Then open the link it prints (usually http://localhost:8501).

The page calls the same agent as the command line (flight_agent.agent.run),
then shows the answer AND how the agent got there: steps, tool calls, time and cost.
"""
import json

import pandas as pd
import streamlit as st

from flight_agent.agent import run
from flight_agent.config import api_key, load_config, resolve
from flight_agent.state import Preferences
from flight_agent.store import load_preferences, save_preferences

st.set_page_config(page_title="Cheapest Flight Finder", page_icon="✈️", layout="wide")

EXAMPLES = {
    "✈️ LAX → New York": "LAX to New York on December 15",
    "🌲 SFO → Seattle": "SFO to Seattle on December 20",
    "📅 Past date": "LAX to Boston on January 5 2020",
    "🛑 Booking request": "book the cheapest LAX to Seattle flight on Dec 20 and pay with my card",
    "❓ Vague request": "cheap flight somewhere warm",
}
STATUS_LOOK = {  # how each final status is shown
    "done": ("success", "Found flights"),
    "needs_clarification": ("info", "The agent needs more details"),
    "refused": ("warning", "Refused by a guardrail"),
    "no_results": ("warning", "No reliable prices found"),
    "error": ("error", "Something went wrong"),
}


# ---------------------------------------------------------------- sidebar: memory + settings
with st.sidebar:
    st.header("Your preferences")
    st.caption("Saved to memory and used on every search.")
    prefs = load_preferences()
    home = st.text_input("Home airport (e.g. LAX)", prefs.home_airport or "")
    bags = st.number_input("Checked bags", 0, 3, prefs.checked_bags)
    stops_choice = st.selectbox("Max stops", ["Any", "Nonstop only", "1 stop", "2 stops"],
                                index=0 if prefs.max_stops is None else prefs.max_stops + 1)
    if st.button("Save preferences"):
        max_stops = None if stops_choice == "Any" else ["Nonstop only", "1 stop", "2 stops"].index(stops_choice)
        save_preferences(Preferences(home_airport=home.strip().upper() or None,
                                     checked_bags=int(bags), max_stops=max_stops))
        st.success("Saved.")

    st.divider()
    use_cache = st.toggle("Use cache (30 min)", value=True,
                          help="A repeat search is reused: much faster and almost free.")
    st.caption(f"Models: {', '.join(f'{k}={v}' for k, v in load_config()['models'].items())}")
    if not api_key():
        st.error("No API key. Set FLIGHT_AGENT_API_KEY before starting the app.")


# ---------------------------------------------------------------- helpers
def show_how_it_worked(trace: dict):
    """The 'glass box' view: what the agent did, step by step."""
    t = trace["totals"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Time", f"{t['duration_ms'] / 1000:.1f} s")
    c2.metric("Cost", f"${t['cost_usd']:.4f}")
    c3.metric("LLM calls", t["llm_calls"])
    c4.metric("Web searches", t["web_searches"])
    c5.metric("From cache", "yes" if t["from_cache"] else "no")

    st.markdown("**Workflow steps** (each step is a traced span)")
    spans = sorted(trace["spans"], key=lambda s: s["start_ms"])
    st.dataframe(pd.DataFrame([{"step": s["name"], "seconds": round(s["duration_ms"] / 1000, 2),
                                "status": s["status"]} for s in spans]),
                 hide_index=True, width="stretch")

    if trace["tool_calls"]:
        st.markdown("**Tool calls**")
        st.dataframe(pd.DataFrame([{"step": c["span"], "tool": c["tool"],
                                    "input": str(c["input"])[:80], "output": str(c["output"])[:80],
                                    "error": c["error"] or ""} for c in trace["tool_calls"]]),
                     hide_index=True, width="stretch")
    if trace["llm_calls"]:
        st.markdown("**Model calls**")
        st.dataframe(pd.DataFrame([{"step": c["step"], "model": c["model"],
                                    "input tokens": c["input_tokens"], "output tokens": c["output_tokens"],
                                    "web searches": c.get("web_searches") or 0, "cost $": c["cost_usd"],
                                    "seconds": round(c["duration_ms"] / 1000, 1)} for c in trace["llm_calls"]]),
                     hide_index=True, width="stretch")
    if trace["result"]["dropped"]:
        st.markdown("**Offers rejected by the guardrails**")
        for reason in trace["result"]["dropped"]:
            st.write("•", reason)
    with st.expander(f"Full trace file: traces/{trace['trace_id']}.json"):
        st.json(trace, expanded=False)


def show_result(state, trace: dict):
    look, label = STATUS_LOOK.get(state.status, ("info", state.status))
    getattr(st, look)(f"**{label}**  ·  status: `{state.status}`")

    if state.status == "done":
        rows = [{"#": i, "Total (USD)": o.true_total_usd, "Fare": o.price_usd,
                 "Bag fee": o.bag_fee_usd, "Airline": o.airline,
                 "Stops": "?" if o.stops is None else ("nonstop" if o.stops == 0 else o.stops),
                 "Depart → Arrive": f"{o.depart_time or '?'} → {o.arrive_time or '?'}",
                 "Source": o.source_url}
                for i, o in enumerate(state.top_offers, 1)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                     column_config={"Source": st.column_config.LinkColumn("Source"),
                                    "Total (USD)": st.column_config.NumberColumn(format="$%.0f"),
                                    "Fare": st.column_config.NumberColumn(format="$%.0f"),
                                    "Bag fee": st.column_config.NumberColumn(format="$%.0f")})
        for i, o in enumerate(state.top_offers, 1):
            for w in o.warnings:
                st.caption(f"⚠️ #{i} {o.airline}: {w}")
        if state.from_cache:
            st.caption("Served from cache (a recent identical search).")
        st.caption("Prices change fast. Confirm on the source site before booking. This agent never books or pays.")
    else:
        st.write(state.message)
    # If the agent asked a question, let the user answer it right here
    if state.status == "needs_clarification" and st.session_state.get("pending"):
        with st.form("clarify"):
            answer = st.text_input("Your answer (e.g. 'from LAX to Miami on Dec 18')")
            if st.form_submit_button("Send answer") and answer.strip():
                search(f"{st.session_state.pending}. {answer.strip()}")
                st.rerun()  # redraw the page with the new result

    st.subheader("How the agent worked")
    show_how_it_worked(trace)


def search(text: str):
    with st.spinner("Searching… a fresh web search takes about 30 seconds."):
        state, trace = run(text, use_cache=use_cache)
    st.session_state.last = (state, trace)
    # Remember the request so a clarifying answer can be added to it
    st.session_state.pending = text if state.status == "needs_clarification" else None


# ---------------------------------------------------------------- main page
st.title("✈️ Cheapest Flight Finder")
st.write("Type a trip in plain English. The agent finds the 3 cheapest flights, adds bag fees for the "
         "**true total**, and links every price to its source. It only searches: it never books or pays.")

tab_search, tab_history = st.tabs(["Search", "Past runs (traces)"])

with tab_search:
    st.caption("Try an example:")
    cols = st.columns(len(EXAMPLES))
    for col, (label, text) in zip(cols, EXAMPLES.items()):
        if col.button(label, width="stretch"):
            st.session_state.trip = text

    with st.form("search"):
        trip = st.text_input("Your trip", key="trip", placeholder="e.g. LAX to New York on December 15")
        go = st.form_submit_button("Find cheapest flights", type="primary")
    if go and trip.strip():
        search(trip.strip())

    if "last" in st.session_state:
        show_result(*st.session_state.last)

with tab_history:
    files = sorted(resolve(load_config()["traces"]["dir"]).glob("*.json"), reverse=True)
    files += sorted(resolve("traces/examples").glob("*.json"))  # sample runs kept in git
    if not files:
        st.info("No runs yet. Do a search first.")
    else:
        traces = [json.loads(f.read_text()) for f in files[:50]]
        st.dataframe(pd.DataFrame([{
            "trace": t["trace_id"], "input": t["input"], "status": t["result"]["status"],
            "seconds": round(t["totals"]["duration_ms"] / 1000, 1), "cost $": t["totals"]["cost_usd"],
            "web searches": t["totals"]["web_searches"], "cache": t["totals"]["from_cache"]} for t in traces]),
            hide_index=True, width="stretch")
        pick = st.selectbox("Open a trace", [f"{t['trace_id']}  ·  {t['input'][:60]}" for t in traces])
        show_how_it_worked(traces[[f"{t['trace_id']}  ·  {t['input'][:60]}" for t in traces].index(pick)])

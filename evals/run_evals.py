"""Run every test case through the real agent and score it automatically.

    python -m evals.run_evals --version v1            # all 15 cases (~$1-3, needs FLIGHT_AGENT_API_KEY)
    python -m evals.run_evals --version v1 --cases grd-01,vag-01

Writes evals/results/<version>.json (every detail) and <version>.md (summary table).
Dates in the dataset are relative ({d+21} = 21 days from today) so cases never go stale.
"""
import argparse
import json
import re
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flight_agent.agent import run  # noqa: E402
from flight_agent.config import load_config  # noqa: E402
from flight_agent.state import Preferences  # noqa: E402
from flight_agent.store import load_preferences, save_preferences  # noqa: E402

EXPECTED_STATUS = {"results": {"done"}, "clarify": {"needs_clarification"}, "refuse": {"refused"}}


def fill_dates(text: str, today: date) -> str:
    return re.sub(r"\{d([+-]\d+)\}", lambda m: (today + timedelta(days=int(m.group(1)))).strftime("%B %d, %Y"), text)


def score_case(case: dict, state, trace: dict) -> dict:
    expect = case["expect"]
    checks = {"behaviour": state.status in EXPECTED_STATUS[expect]}
    if expect == "results":
        q = state.query
        checks["route"] = bool(q) and bool(set(q.origin_codes) & set(case["origin"])) \
            and bool(set(q.destination_codes) & set(case["destination"]))
        checks["has_offers"] = len(state.top_offers) > 0
        checks["all_cited"] = bool(state.top_offers) and all(o.source_url in state.message for o in state.top_offers)
        checks["disclaimer"] = "Prices change fast" in state.message
        if case.get("needs_bag_fee"):
            checks["bag_fee_applied"] = bool(state.top_offers) and any(
                o.bag_fee_usd is not None for o in state.top_offers)
    totals = trace["totals"]
    return {
        "id": case["id"], "group": case["group"], "input": case["input"], "expect": expect,
        "status": state.status, "checks": checks, "passed": all(checks.values()),
        "offers": [{"airline": o.airline, "price_usd": o.price_usd, "true_total_usd": o.true_total_usd,
                    "verified": o.price_verified, "url": o.source_url} for o in state.top_offers],
        "dropped": state.dropped, "cost_usd": totals["cost_usd"], "seconds": round(totals["duration_ms"] / 1000, 1),
        "web_searches": totals["web_searches"], "trace_id": state.trace_id, "message": state.message,
        # Filled in by hand after checking Google Flights (see README):
        "manual_cheapest_on_google_flights": None, "manual_within_10_percent": None,
    }


def summarize(results: list[dict]) -> dict:
    def rate(key):
        vals = [r["checks"][key] for r in results if key in r["checks"]]
        return round(100 * sum(vals) / len(vals), 1) if vals else None

    offers = [o for r in results for o in r["offers"]]
    seconds = [r["seconds"] for r in results if r["expect"] == "results"]
    return {
        "cases": len(results),
        "pass_rate": round(100 * sum(r["passed"] for r in results) / len(results), 1),
        "behaviour_accuracy": rate("behaviour"),
        "route_accuracy": rate("route"),
        "results_with_offers": rate("has_offers"),
        "citation_rate": rate("all_cited"),
        "bag_fee_applied": rate("bag_fee_applied"),
        "price_verified_rate": round(100 * sum(o["verified"] for o in offers) / len(offers), 1) if offers else None,
        "offers_dropped_by_guardrails": sum(len(r["dropped"]) for r in results),
        "total_cost_usd": round(sum(r["cost_usd"] for r in results), 4),
        "avg_cost_per_search_case": round(statistics.mean(
            [r["cost_usd"] for r in results if r["expect"] == "results"] or [0]), 4),
        "median_seconds_search_case": statistics.median(seconds) if seconds else None,
        "max_seconds": max((r["seconds"] for r in results), default=None),
        "by_group": {g: f"{sum(r['passed'] for r in results if r['group'] == g)}/"
                        f"{sum(1 for r in results if r['group'] == g)}"
                     for g in sorted({r["group"] for r in results})},
    }


def write_markdown(path: Path, version: str, summary: dict, results: list[dict]):
    lines = [f"# Eval results: {version}", "", f"Prompt version: {load_config()['prompt_version']}", "",
             "| Metric | Value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in summary.items() if k != "by_group"]
    lines += ["", "| Group | Passed |", "|---|---|"] + [f"| {g} | {v} |" for g, v in summary["by_group"].items()]
    lines += ["", "| Case | Expect | Status | Pass | Cheapest (USD) | Cost | Seconds | Failed checks |",
              "|---|---|---|---|---|---|---|---|"]
    for r in results:
        cheapest = f"${r['offers'][0]['true_total_usd']:,.0f}" if r["offers"] else "-"
        failed = ", ".join(k for k, v in r["checks"].items() if not v) or "-"
        lines.append(f"| {r['id']} | {r['expect']} | {r['status']} | {'✅' if r['passed'] else '❌'} | "
                     f"{cheapest} | ${r['cost_usd']:.3f} | {r['seconds']} | {failed} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="label for this run, e.g. v1")
    ap.add_argument("--cases", help="comma-separated case ids to run (default: all)")
    args = ap.parse_args()

    today = date.today()
    cases = [json.loads(line) for line in (ROOT / "evals" / "dataset.jsonl").read_text().splitlines() if line.strip()]
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [c for c in cases if c["id"] in wanted]

    original_prefs = load_preferences()
    results = []
    try:
        for case in cases:
            case["input"] = fill_dates(case["text"], today)
            save_preferences(Preferences(**case.get("prefs", {})))
            print(f"[{case['id']}] {case['input']}", flush=True)
            state, trace = run(case["input"], today=today, use_cache=False)
            r = score_case(case, state, trace)
            results.append(r)
            print(f"   -> {r['status']} | {'PASS' if r['passed'] else 'FAIL'} | ${r['cost_usd']:.3f} | {r['seconds']}s",
                  flush=True)
    finally:
        save_preferences(original_prefs)  # put the user's real preferences back

    summary = summarize(results)
    out = ROOT / "evals" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.version}.json").write_text(json.dumps(
        {"version": args.version, "date": str(today), "prompt_version": load_config()["prompt_version"],
         "models": load_config()["models"], "summary": summary, "results": results}, indent=2), encoding="utf-8")
    write_markdown(out / f"{args.version}.md", args.version, summary, results)
    print("\n" + json.dumps(summary, indent=2))
    print(f"\nSaved evals/results/{args.version}.json and .md")


if __name__ == "__main__":
    main()

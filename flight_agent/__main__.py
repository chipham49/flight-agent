"""Command line:  python -m flight_agent "LAX to New York, Dec 10"

Other commands:
  python -m flight_agent --prefs                         show saved preferences
  python -m flight_agent --set home_airport=LAX          remember a preference
  python -m flight_agent --set checked_bags=1 --set max_stops=1
  python -m flight_agent "..." --no-cache                skip the cache
"""
import argparse
import os
import sys

from .config import load_config
from .store import load_preferences, save_preferences


def main():
    ap = argparse.ArgumentParser(prog="flight_agent", description="Find the 3 cheapest flights for a trip.")
    ap.add_argument("trip", nargs="?", help='e.g. "LAX to New York, Dec 10"')
    ap.add_argument("--no-cache", action="store_true", help="always search fresh")
    ap.add_argument("--prefs", action="store_true", help="show saved preferences")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="save a preference: home_airport, checked_bags, max_stops")
    args = ap.parse_args()

    if args.set or args.prefs:
        prefs = load_preferences()
        for item in args.set:
            key, _, value = item.partition("=")
            if key not in prefs.model_fields:
                sys.exit(f"Unknown preference '{key}'. Use: {', '.join(prefs.model_fields)}")
            setattr(prefs, key, None if value.lower() in ("", "none") else
                    (int(value) if key in ("checked_bags", "max_stops") else value.upper()))
        if args.set:
            save_preferences(prefs)
        print(prefs.model_dump())
        return

    if not args.trip:
        ap.print_help()
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Add it as an environment variable (see README).")

    from .agent import run  # imported here so --help works without dependencies configured

    text = args.trip
    for _ in range(load_config()["limits"]["max_clarifications"] + 1):
        state, trace = run(text, use_cache=not args.no_cache)
        print("\n" + state.message)
        t = trace["totals"]
        print(f"\n[trace {state.trace_id} | {t['duration_ms'] / 1000:.1f}s | ${t['cost_usd']:.4f} | "
              f"{t['llm_calls']} LLM calls, {t['web_searches']} web searches | status: {state.status}]")
        if state.status != "needs_clarification" or not sys.stdin.isatty():
            break
        answer = input("> ").strip()
        if not answer:
            break
        text = f"{text}. {answer}"


if __name__ == "__main__":
    main()

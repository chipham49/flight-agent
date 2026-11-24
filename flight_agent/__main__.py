"""Command line:  python -m flight_agent "LAX to New York, Dec 10"

Other commands:
  python -m flight_agent --prefs                         show saved preferences
  python -m flight_agent --set home_airport=LAX          remember a preference
  python -m flight_agent --set checked_bags=1 --set max_stops=1
  python -m flight_agent "..." --no-cache                skip the cache
  python -m flight_agent --check-key                     test the API key (free: lists models)
"""
import argparse
import sys

from .config import API_BASE_URL, api_key, load_config
from .store import load_preferences, save_preferences


def check_key():
    """Free check that the API key works and can see the models in config.yaml."""
    if not api_key():
        sys.exit("No API key found. Set FLIGHT_AGENT_API_KEY (or ANTHROPIC_API_KEY when running locally); see README.")
    import anthropic

    try:
        available = {m.id for m in anthropic.Anthropic(api_key=api_key(), base_url=API_BASE_URL).models.list()}
    except anthropic.AuthenticationError:
        sys.exit("The API key was rejected (401). Check it was copied fully and is not revoked.")
    except anthropic.PermissionDeniedError:
        sys.exit("The API key has no permission for this (403). Check the key's workspace in the Console.")
    except anthropic.APIConnectionError as e:
        sys.exit(f"Could not reach the Anthropic API: {e}")
    print("API key works.")
    for step, model in load_config()["models"].items():
        print(f"  {step:8} {model:22} {'OK' if model in available else 'NOT AVAILABLE to this key'}")


def main():
    ap = argparse.ArgumentParser(prog="flight_agent", description="Find the 3 cheapest flights for a trip.")
    ap.add_argument("trip", nargs="?", help='e.g. "LAX to New York, Dec 10"')
    ap.add_argument("--no-cache", action="store_true", help="always search fresh")
    ap.add_argument("--prefs", action="store_true", help="show saved preferences")
    ap.add_argument("--check-key", action="store_true", help="test the API key (free, no tokens used)")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="save a preference: home_airport, checked_bags, max_stops")
    args = ap.parse_args()

    if args.check_key:
        check_key()
        return

    if args.set or args.prefs:
        prefs = load_preferences()
        for item in args.set:
            key, _, value = item.partition("=")
            if key not in type(prefs).model_fields:
                sys.exit(f"Unknown preference '{key}'. Use: {', '.join(type(prefs).model_fields)}")
            setattr(prefs, key, None if value.lower() in ("", "none") else
                    (int(value) if key in ("checked_bags", "max_stops") else value.upper()))
        if args.set:
            save_preferences(prefs)
        print(prefs.model_dump())
        return

    if not args.trip:
        ap.print_help()
        return
    if not api_key():
        sys.exit("No API key found. Set FLIGHT_AGENT_API_KEY (or ANTHROPIC_API_KEY when running locally); see README.")

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

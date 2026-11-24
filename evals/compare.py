"""Compare two eval runs and fail if quality got worse (regression check).

    python -m evals.compare v1 v2

Prints a before/after table and writes evals/results/compare_v1_v2.md.
Exit code 1 if a key quality metric dropped, so it can gate a pull request.
"""
import json
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / "results"

# Metrics where higher is better, and how many points they may drop before we call it a regression
QUALITY = {"pass_rate": 0, "behaviour_accuracy": 0, "route_accuracy": 0, "citation_rate": 0,
           "results_with_offers": 10, "price_verified_rate": 10}
LOWER_IS_BETTER = {"total_cost_usd", "avg_cost_per_search_case", "median_seconds_search_case", "max_seconds"}


def main(a: str, b: str) -> int:
    old = json.loads((RESULTS / f"{a}.json").read_text())["summary"]
    new = json.loads((RESULTS / f"{b}.json").read_text())["summary"]
    lines = [f"# Comparison: {a} vs {b}", "", f"| Metric | {a} | {b} | Change |", "|---|---|---|---|"]
    regressions = []
    for key in old:
        if key == "by_group":
            continue
        x, y = old.get(key), new.get(key)
        change = ""
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            diff = round(y - x, 4)
            better = diff < 0 if key in LOWER_IS_BETTER else diff > 0
            change = f"{diff:+} {'✅' if better else ('' if diff == 0 else '⚠️')}"
            if key in QUALITY and diff < -QUALITY[key]:
                regressions.append(f"{key} dropped {x} -> {y}")
        lines.append(f"| {key} | {x} | {y} | {change} |")
    lines += ["", "| Group | " + a + " | " + b + " |", "|---|---|---|"]
    for g in sorted(set(old["by_group"]) | set(new["by_group"])):
        lines.append(f"| {g} | {old['by_group'].get(g, '-')} | {new['by_group'].get(g, '-')} |")
    lines += ["", "**Regression check:** " + ("FAILED: " + "; ".join(regressions) if regressions else "passed ✅")]
    report = "\n".join(lines) + "\n"
    (RESULTS / f"compare_{a}_{b}.md").write_text(report, encoding="utf-8")
    print(report)
    return 1 if regressions else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python -m evals.compare v1 v2")
    sys.exit(main(sys.argv[1], sys.argv[2]))

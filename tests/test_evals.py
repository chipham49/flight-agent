"""Checks that the eval scoring and comparison logic work (using the fake LLM)."""
import json
from datetime import date

from conftest import FakeLLM, offer, trip
from evals import compare
from evals.run_evals import fill_dates, score_case, summarize
from flight_agent.agent import run


def test_fill_dates_is_relative_to_today():
    assert fill_dates("on {d+1}", date(2026, 12, 31)) == "on January 01, 2027"


def test_scoring_and_summary():
    case = {"id": "x", "group": "domestic", "input": "LAX to NYC", "expect": "results",
            "origin": ["LAX"], "destination": ["JFK"]}
    state, trace = run("LAX to NYC", today=date(2026, 11, 24), llm=FakeLLM(trip(), [offer()]))
    r = score_case(case, state, trace)
    assert r["passed"], r["checks"]
    s = summarize([r])
    assert s["pass_rate"] == 100 and s["by_group"] == {"domestic": "1/1"}


def test_compare_flags_regression(tmp_path, monkeypatch):
    monkeypatch.setattr(compare, "RESULTS", tmp_path)
    base = {"pass_rate": 90, "behaviour_accuracy": 100, "route_accuracy": 100, "citation_rate": 100,
            "results_with_offers": 80, "price_verified_rate": 50, "total_cost_usd": 2.0, "by_group": {}}
    (tmp_path / "v1.json").write_text(json.dumps({"summary": base}))
    (tmp_path / "v2.json").write_text(json.dumps({"summary": {**base, "pass_rate": 95, "total_cost_usd": 1.5}}))
    (tmp_path / "v3.json").write_text(json.dumps({"summary": {**base, "route_accuracy": 90}}))
    assert compare.main("v1", "v2") == 0
    assert compare.main("v1", "v3") == 1

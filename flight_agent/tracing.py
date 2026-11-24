"""Observability: records everything one run does and saves it as a JSON trace.

A trace holds:
  - spans: one per workflow step, with start time, duration and attributes
  - llm_calls: every model call with the full prompt, response, tokens and cost
  - tool_calls: every tool call (web search, airport lookup, RAG) with input/output
  - totals: overall cost, tokens and duration

Open traces/<trace_id>.json to see exactly what happened in a run.
"""
import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import load_config, resolve


class Tracer:
    def __init__(self, user_input: str, metadata: dict | None = None):
        self.trace_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.started = time.perf_counter()
        self.data = {
            "trace_id": self.trace_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input": user_input,
            "metadata": metadata or {},
            "spans": [],
            "llm_calls": [],
            "tool_calls": [],
        }
        self._current_span: str | None = None

    @contextmanager
    def span(self, name: str, **attributes):
        """Time one step of the workflow. Use as: `with tracer.span("parse"): ...`"""
        record = {"name": name, "start_ms": self._now_ms(), "attributes": attributes, "status": "ok"}
        previous, self._current_span = self._current_span, name
        try:
            yield record["attributes"]
        except Exception as e:  # recorded, then re-raised so the caller can handle it
            record["status"] = "error"
            record["error"] = f"{type(e).__name__}: {e}"
            raise
        finally:
            record["duration_ms"] = round(self._now_ms() - record["start_ms"], 1)
            self.data["spans"].append(record)
            self._current_span = previous

    def llm_call(self, **record):
        record["span"] = self._current_span
        self.data["llm_calls"].append(record)

    def tool_call(self, tool: str, inputs, outputs, duration_ms: float | None = None, error: str | None = None):
        self.data["tool_calls"].append({
            "span": self._current_span, "tool": tool, "input": inputs, "output": outputs,
            "duration_ms": duration_ms, "error": error,
        })

    def finish(self, state) -> dict:
        calls = self.data["llm_calls"]
        self.data["totals"] = {
            "duration_ms": round(self._now_ms(), 1),
            "cost_usd": round(sum(c.get("cost_usd", 0) for c in calls), 5),
            "input_tokens": sum(c.get("input_tokens", 0) for c in calls),
            "output_tokens": sum(c.get("output_tokens", 0) for c in calls),
            "llm_calls": len(calls),
            "tool_calls": len(self.data["tool_calls"]),
            "web_searches": sum(c.get("web_searches", 0) for c in calls),
            "steps": state.steps_taken,
            "from_cache": state.from_cache,
        }
        self.data["result"] = {
            "status": state.status,
            "message": state.message,
            "top_offers": [o.model_dump() for o in state.top_offers],
            "dropped": state.dropped,
        }
        return self.data

    def save(self) -> str:
        folder = resolve(load_config()["traces"]["dir"])
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{self.trace_id}.json"
        path.write_text(json.dumps(self.data, indent=2, default=str), encoding="utf-8")
        return str(path)

    def _now_ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000

"""All calls to Claude go through this file, so every call is traced and costed.

Two kinds of call:
  - parse_structured(): a cheap model returns data in a fixed shape (Pydantic model)
  - search_web():       a stronger model uses Claude's web search tool
"""
import time

import anthropic

from .config import load_config


def cost_of(model: str, usage) -> float:
    """Dollar cost of one call, from the token counts in response.usage."""
    prices = load_config()["pricing"]
    p = prices.get(model, prices["claude-sonnet-5-5"])
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    cost = (usage.input_tokens * p["input"] + cached * p.get("cache_read", 0)
            + usage.output_tokens * p["output"]) / 1_000_000
    server = getattr(usage, "server_tool_use", None)
    searches = (getattr(server, "web_search_requests", 0) or 0) if server else 0
    return cost + searches * prices["web_search_per_1000"] / 1000


def _searches(usage) -> int:
    server = getattr(usage, "server_tool_use", None)
    return (getattr(server, "web_search_requests", 0) or 0) if server else 0


class LLM:
    """Thin wrapper around the Anthropic SDK. Tests swap this for a fake."""

    def __init__(self, tracer, client: anthropic.Anthropic | None = None):
        # Anthropic() reads ANTHROPIC_API_KEY from the environment. Never hardcode it.
        self.client = client or anthropic.Anthropic(max_retries=2, timeout=90)
        self.tracer = tracer
        self.cfg = load_config()

    def parse_structured(self, step: str, system: str, user: str, schema):
        """Ask a model for output matching `schema` (a Pydantic model). Returns (parsed, cost)."""
        model = self.cfg["models"][step]
        started = time.perf_counter()
        response = self.client.messages.parse(
            model=model,
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
            output_config={"effort": self.cfg["effort"][step]},
        )
        cost = cost_of(model, response.usage)
        self.tracer.llm_call(
            step=step, model=model, system=system, prompt=user,
            response=response.parsed_output.model_dump() if response.parsed_output else None,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens,
            cost_usd=round(cost, 6), duration_ms=round((time.perf_counter() - started) * 1000, 1),
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("The model declined this request.")
        return response.parsed_output, cost

    def search_web(self, system: str, user: str):
        """Run a web-search conversation. Returns (notes_text, urls_seen, cited_texts, cost)."""
        model = self.cfg["models"]["search"]
        limits = self.cfg["limits"]
        tools = [{"type": "web_search_20260209", "name": "web_search",
                  "max_uses": limits["max_web_searches"]}]
        messages = [{"role": "user", "content": user}]
        notes, urls, cited, total_cost = [], [], [], 0.0

        # pause_turn means the server-side search loop paused; resume a bounded number of times.
        for _ in range(limits["max_pause_continuations"] + 1):
            started = time.perf_counter()
            response = self.client.beta.messages.create(
                model=model,
                max_tokens=16000,
                cache_control={"type": "ephemeral"},   # caches the fixed system prompt + tools
                system=system,
                tools=tools,
                messages=messages,
                output_config={"effort": self.cfg["effort"]["search"]},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",                   # if Sonnet declines, the API retries on a fallback model
            )
            cost = cost_of(response.model, response.usage)
            total_cost += cost
            for block in response.content:
                if block.type == "web_search_tool_result" and isinstance(block.content, list):
                    urls += [r.url for r in block.content if getattr(r, "url", None)]
                elif block.type == "text":
                    notes.append(block.text)
                    for c in getattr(block, "citations", None) or []:
                        if getattr(c, "url", None):
                            urls.append(c.url)
                        if getattr(c, "cited_text", None):
                            cited.append(c.cited_text)
            self.tracer.llm_call(
                step="search", model=response.model, system=system, prompt=user,
                response="\n".join(notes), stop_reason=response.stop_reason,
                input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens,
                web_searches=_searches(response.usage), cost_usd=round(cost, 6),
                duration_ms=round((time.perf_counter() - started) * 1000, 1),
            )
            if response.stop_reason == "refusal":
                raise RuntimeError("The model declined this search.")
            if response.stop_reason != "pause_turn":
                break
            messages = [{"role": "user", "content": user},
                        {"role": "assistant", "content": response.content}]

        return "\n".join(notes), list(dict.fromkeys(urls)), cited, total_cost

"""RAG: search the airline knowledge base (knowledge/*.md) for bag-fee rules.

How it works:
  1. Load:     each Markdown file has a header (airline, aliases, source_url, collected_on)
               and is split into sections (one chunk per "## " heading).
  2. Rewrite:  the question is expanded with synonyms ("bag" -> "baggage luggage checked")
               and the airline's other names, so short questions still match.
  3. Filter:   if we know the airline, only that airline's chunks are searched.
  4. Rank:     BM25 scoring (the classic search-engine formula), top-k chunks returned.
  5. Cite:     every result carries its source_url and collected_on date.

BM25 is written out here in a few lines, so there are no extra libraries to install.
"""
import math
import re
from dataclasses import dataclass
from functools import lru_cache

from ..config import load_config, resolve

SYNONYMS = {
    "bag": ["baggage", "luggage", "checked", "suitcase"],
    "bags": ["baggage", "luggage", "checked", "suitcase"],
    "suitcase": ["checked", "baggage", "bag"],
    "carry": ["carry-on", "cabin", "overhead"],
    "fee": ["cost", "price", "charge"],
    "basic": ["basic", "economy", "restrictions"],
    "connection": ["layover", "minimum", "connecting"],
}


@dataclass
class Chunk:
    airline: str
    aliases: list[str]
    section: str
    text: str
    source_url: str
    collected_on: str
    file: str


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9$]+(?:-[a-z0-9]+)?", text.lower())


def _parse_file(path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8")
    header, _, body = raw.partition("\n---\n")
    meta = {}
    for line in header.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    aliases = [a.strip().lower() for a in meta.get("aliases", "").split(",") if a.strip()]
    chunks = []
    for part in re.split(r"\n(?=## )", body.strip()):
        title = part.splitlines()[0].lstrip("# ").strip()
        chunks.append(Chunk(meta.get("airline", path.stem), aliases, title, part.strip(),
                            meta.get("source_url", ""), meta.get("collected_on", ""), path.name))
    return chunks


@lru_cache
def load_chunks() -> list[Chunk]:
    folder = resolve(load_config()["knowledge"]["dir"])
    chunks = []
    for path in sorted(folder.glob("*.md")):
        chunks += _parse_file(path)
    return chunks


def match_airline(name: str) -> str | None:
    """Map an airline name from search results ('Delta Air Lines', 'DL') to a knowledge file."""
    n = (name or "").lower().strip()
    if not n:
        return None
    for c in load_chunks():
        if not c.aliases:  # general guidance files are not an airline
            continue
        names = [c.airline.lower()] + c.aliases
        words = set(_tokens(n))
        for a in names:
            if len(a) <= 2:  # airline codes like "ha" must match a whole word, not part of "etihad"
                if a in words:
                    return c.airline
            elif n == a or re.search(rf"\b{re.escape(a)}\b", n) or (len(n) > 3 and n in a):
                return c.airline
    return None


def rewrite_query(question: str, airline: str | None) -> list[str]:
    words = _tokens(question)
    expanded = list(words)
    for w in words:
        expanded += SYNONYMS.get(w, [])
    if airline:
        expanded += _tokens(airline)
    return expanded


def retrieve(question: str, airline: str | None = None, top_k: int | None = None) -> list[dict]:
    top_k = top_k or load_config()["knowledge"]["top_k"]
    canonical = match_airline(airline) if airline else None
    pool = [c for c in load_chunks() if canonical is None or c.airline == canonical]
    if not pool:
        return []
    query = rewrite_query(question, canonical or airline)

    # BM25
    docs = [_tokens(c.section + " " + c.text) for c in pool]
    avg_len = sum(map(len, docs)) / len(docs)
    n = len(docs)
    k1, b = 1.5, 0.75
    scores = []
    for doc in docs:
        score = 0.0
        for term in set(query):
            tf = doc.count(term)
            if not tf:
                continue
            df = sum(1 for d in docs if term in d)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / avg_len))
        scores.append(score)

    ranked = sorted(zip(scores, pool), key=lambda x: x[0], reverse=True)
    return [
        {"airline": c.airline, "section": c.section, "text": c.text, "score": round(s, 3),
         "source_url": c.source_url, "collected_on": c.collected_on, "file": c.file}
        for s, c in ranked[:top_k] if s > 0
    ]


def checked_bag_fee(airline: str, bags: int) -> dict | None:
    """Structured lookup used by the agent: fee in USD for `bags` checked bags, with citation.

    Reads a line like `first_checked_bag_usd: 35` from the airline's file.
    """
    if bags <= 0:
        return {"fee_usd": 0.0, "source_url": None, "note": "no checked bags requested"}
    if not match_airline(airline):  # never borrow another airline's fee
        return None
    hits = retrieve("checked bag fee first second", airline=airline, top_k=3)
    if not hits:
        return None
    text = "\n".join(h["text"] for h in hits)
    first = re.search(r"first_checked_bag_usd:\s*([\d.]+)", text)
    second = re.search(r"second_checked_bag_usd:\s*([\d.]+)", text)
    if not first:
        return None
    f = float(first.group(1))
    s = float(second.group(1)) if second else f
    fee = f + s * max(0, bags - 1)
    return {"fee_usd": round(fee, 2), "source_url": hits[0]["source_url"],
            "collected_on": hits[0]["collected_on"], "airline": hits[0]["airline"]}

"""Grounded research — a free Perplexity-style answer.

Searches the live web (DuckDuckGo, or Brave if keyed), then Groq synthesizes a
concise answer that cites the sources [1][2]. Returns the answer + citation list.
"""
import cache
from services import llm
from services.strategy import websearch

_TTL = 60 * 60

_SYSTEM = (
    "You are a research analyst. Answer the question using ONLY the numbered web "
    "sources provided. Cite claims inline with [n]. Be concise (3-5 sentences), "
    "specific, and current. If the sources don't cover it, say so briefly. "
    "Do not invent facts or sources."
)


def grounded_answer(question, n_sources=5):
    """Return {ok, answer, citations:[{n,title,url}]}."""
    if not llm.configured():
        return {"ok": False, "answer": "AI is not configured.", "citations": []}

    key = f"research:{question.lower().strip()}"
    cached = cache.get(key)
    if cached:
        return cached

    results = websearch.search(question, n_sources)
    if not results:
        return {"ok": False, "answer": "Couldn't reach the web to research this right now.",
                "citations": []}

    sources, block = [], []
    for i, r in enumerate(results[:n_sources], 1):
        sources.append({"n": i, "title": r.get("title", ""), "url": r.get("url", "")})
        block.append(f"[{i}] {r.get('title','')} — {r.get('description','')} ({r.get('url','')})")

    user = f"Question: {question}\n\nSources:\n" + "\n".join(block)
    res = llm.chat(_SYSTEM, user, max_tokens=400, temperature=0.4)
    if not res.get("ok"):
        return {"ok": False, "answer": f"Research unavailable ({res.get('error')}).",
                "citations": sources}

    out = {"ok": True, "answer": res["text"], "citations": sources,
           "model": res.get("model")}
    cache.set(key, out, _TTL)
    return out

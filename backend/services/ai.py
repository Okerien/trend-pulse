"""Groq-powered intelligence that informs the Tracker and Niche Explorer:
per-keyword reads, keyword suggestions, and niche expansion. Fast + cached.
"""
import json
import re

import cache
from services import llm

_TTL = 6 * 60 * 60


def _parse_json(text):
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    for pat in (t, t[t.find("{"):t.rfind("}") + 1] if "{" in t else "",
                t[t.find("["):t.rfind("]") + 1] if "[" in t else ""):
        if not pat:
            continue
        try:
            return json.loads(pat)
        except Exception:  # noqa: BLE001
            continue
    return None


def _read_key(kw):
    bucket = round((kw.get("momentum") or 0) / 10)
    return (f"airead:{kw.get('keyword','').lower()}:{bucket}:{kw.get('band','')}:"
            f"{int(bool(kw.get('breakout')))}:{kw.get('seasonality')}")


def _signals(kw):
    s = []
    if kw.get("momentum") is not None:
        s.append(f"momentum {kw['momentum']}/100 ({kw.get('band','')})")
    if kw.get("change_pct") is not None:
        s.append(f"{kw['change_pct']:+}% over period")
    if kw.get("breakout"):
        s.append("breakout")
    if kw.get("seasonality"):
        s.append(str(kw["seasonality"]))
    e = kw.get("enrich") or {}
    for label, v in (("news", e.get("news")), ("reddit", e.get("reddit")),
                     ("wiki views", (e.get("wikipedia") or {}).get("total"))):
        if v is not None:
            s.append(f"{label} {v}")
    return ", ".join(s) or "limited data"


_READ_SYSTEM = ("You are a sharp trend analyst for a marketing agency. For each "
                "keyword, write ONE punchy, specific, actionable sentence (max 24 "
                "words) on what it means and what to do. No preamble, no quotes.")


def keyword_read(kw):
    """One read for a single keyword."""
    if not llm.configured():
        return {"ok": False, "read": ""}
    cached = cache.get(_read_key(kw))
    if cached:
        return cached
    res = llm.chat(_READ_SYSTEM,
                   f"Keyword: \"{kw.get('keyword')}\". Signals: {_signals(kw)}.",
                   max_tokens=70, temperature=0.6)
    if not res.get("ok"):
        return {"ok": False, "read": ""}
    out = {"ok": True, "read": res["text"].strip().strip('"')}
    cache.set(_read_key(kw), out, _TTL)
    return out


def keyword_reads(kws):
    """Batch reads — one Groq call for all cache-misses. Avoids N concurrent calls."""
    reads, misses = {}, []
    for kw in kws:
        c = cache.get(_read_key(kw))
        if c:
            reads[kw.get("keyword")] = c["read"]
        else:
            misses.append(kw)
    if misses and llm.configured():
        lines = [f"{i+1}. \"{kw.get('keyword')}\": {_signals(kw)}"
                 for i, kw in enumerate(misses)]
        system = (_READ_SYSTEM + " Return ONLY a JSON object mapping each exact "
                  "keyword to its sentence.")
        res = llm.chat(system, "Keywords and signals:\n" + "\n".join(lines),
                       max_tokens=80 * len(misses) + 100, temperature=0.6, timeout=60)
        data = _parse_json(res.get("text", "")) if res.get("ok") else None
        if isinstance(data, dict):
            for kw in misses:
                k = kw.get("keyword")
                val = data.get(k)
                if isinstance(val, str) and val.strip():
                    read = val.strip().strip('"')
                    reads[k] = read
                    cache.set(_read_key(kw), {"ok": True, "read": read}, _TTL)
    return {"reads": reads}


def correlation_note(pairs):
    """One-paragraph plain-English read of the correlation matrix."""
    if not llm.configured() or not pairs:
        return {"ok": False, "note": ""}
    key = "aicorr:" + ",".join(sorted(f"{p['a']}~{p['b']}~{p['r']}" for p in pairs))
    cached = cache.get(key)
    if cached:
        return cached
    lines = [f"{p['a']} & {p['b']}: r={p['r']}" for p in pairs]
    system = ("You are a marketing data analyst. In 2 concise sentences, explain "
              "what these keyword correlations mean for content/audience strategy. "
              "No preamble.")
    res = llm.chat(system, "Correlations:\n" + "\n".join(lines), max_tokens=130, temperature=0.5)
    if not res.get("ok"):
        return {"ok": False, "note": ""}
    out = {"ok": True, "note": res["text"].strip()}
    cache.set(key, out, _TTL)
    return out


def suggest_keywords(seed, n=6):
    """Related, high-potential keywords to also track."""
    if not llm.configured() or not seed:
        return {"ok": False, "keywords": []}
    key = f"aisuggest:{seed.lower()}:{n}"
    cached = cache.get(key)
    if cached:
        return cached
    system = ("You suggest keywords for trend tracking. Return ONLY a JSON array "
              "of strings, no prose.")
    user = (f"Give {n} closely related, high-search-potential keywords a marketer "
            f"should track alongside \"{seed}\". Specific multi-word phrases, not generic.")
    res = llm.chat(system, user, max_tokens=200, temperature=0.7)
    arr = _parse_json(res.get("text", "")) if res.get("ok") else None
    kws = [str(x).strip() for x in arr if str(x).strip()][:n] if isinstance(arr, list) else []
    out = {"ok": bool(kws), "keywords": kws}
    if kws:
        cache.set(key, out, _TTL)
    return out


def niche_expand(niche):
    """State-of-the-niche + curated high-opportunity keywords."""
    if not llm.configured() or not niche:
        return {"ok": False, "state": "", "keywords": []}
    key = f"ainiche:{niche.lower()}"
    cached = cache.get(key)
    if cached:
        return cached
    system = ("You are a marketing strategist. Return ONLY JSON: "
              '{"state": "<one vivid sentence on this niche right now>", '
              '"keywords": ["<10 specific high-opportunity keywords to track>"]}.')
    res = llm.chat(system, f"Niche: {niche}", max_tokens=320, temperature=0.7)
    data = _parse_json(res.get("text", "")) if res.get("ok") else None
    if not isinstance(data, dict):
        return {"ok": False, "state": "", "keywords": []}
    out = {"ok": True, "state": str(data.get("state", "")),
           "keywords": [str(k).strip() for k in (data.get("keywords") or []) if str(k).strip()][:10]}
    cache.set(key, out, _TTL)
    return out

"""LLM service. Prefers Groq (free, fast, Llama-3.3-70B) and falls back to the
Hugging Face Inference router. Both use the OpenAI-compatible chat schema.

The free key lives only here, server-side. Fails soft everywhere.
"""
import requests

import cache
from config import (HUGGINGFACE_API_TOKEN, HF_MODEL, TTL_SUMMARY,
                    GROQ_API_KEY, GROQ_MODEL)

_HF_URL = "https://router.huggingface.co/v1/chat/completions"
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_TIMEOUT = 40


def provider():
    """Return (name, url, headers, model) for the active provider, or None."""
    if GROQ_API_KEY:
        return ("groq", _GROQ_URL, {"Authorization": f"Bearer {GROQ_API_KEY}"}, GROQ_MODEL)
    if HUGGINGFACE_API_TOKEN:
        return ("hf", _HF_URL, {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}, HF_MODEL)
    return None


def configured():
    return provider() is not None


def chat(system, user, max_tokens=600, temperature=0.6, timeout=None):
    """Generic chat-completion. Returns {"ok": bool, "text"|"error": str, "model": str}."""
    p = provider()
    if not p:
        return {"ok": False, "error": "no_key"}
    name, url, headers, model = p
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=timeout or _TIMEOUT)
        if r.status_code == 402:
            return {"ok": False, "error": "credits_exhausted"}
        if r.status_code == 401:
            return {"ok": False, "error": "invalid_key"}
        if r.status_code == 429:
            return {"ok": False, "error": "rate_limited"}
        if r.status_code != 200:
            detail = ""
            try:
                detail = r.json().get("error", {}).get("message", "")
            except Exception:  # noqa: BLE001
                pass
            return {"ok": False, "error": f"{name}_{r.status_code} {detail}".strip()}
        text = (r.json().get("choices", [{}])[0].get("message", {})
                .get("content", "")).strip()
        if not text:
            return {"ok": False, "error": "empty"}
        return {"ok": True, "text": text, "model": model}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__}


def _build_user_message(payload):
    lines = []
    for kw in payload.get("keywords", []):
        parts = [f"- \"{kw.get('keyword')}\":"]
        if kw.get("change_pct") is not None:
            parts.append(f"{kw['change_pct']:+}% over the period")
        if kw.get("momentum") is not None:
            parts.append(f"momentum {kw['momentum']}/100")
        if kw.get("breakout"):
            parts.append("BREAKOUT")
        if kw.get("seasonality"):
            parts.append(str(kw["seasonality"]))
        if kw.get("best_time"):
            parts.append(f"peaks {kw['best_time']}")
        lines.append(" ".join(parts))
    text = "Search-trend data:\n" + "\n".join(lines)
    for corr in (payload.get("correlations") or [])[:1]:
        text += (f"\n'{corr['a']}' and '{corr['b']}' have a correlation "
                 f"coefficient of {corr['r']}.")
    return text


_SUMMARY_SYSTEM = (
    "You are a marketing analyst for a digital agency. Based ONLY on the "
    "search-trend data you are given, write a concise, client-ready "
    "recommendation of exactly three sentences in plain English. Be specific "
    "and actionable. Do not invent numbers or facts not present in the data."
)


def summarise(payload):
    """Feature 23 — AI trend summary. Returns {"summary": str, "ok": bool}."""
    if not configured():
        return {"ok": False,
                "summary": "AI summary unavailable — no LLM key configured."}
    cache_key = "summary:" + ",".join(
        sorted(k.get("keyword", "") for k in payload.get("keywords", [])))
    cached = cache.get(cache_key)
    if cached:
        return cached
    res = chat(_SUMMARY_SYSTEM, _build_user_message(payload),
               max_tokens=260, temperature=0.6)
    if not res.get("ok"):
        msg = {
            "rate_limited": "The AI model is busy — try again in a moment.",
            "credits_exhausted": "AI summary unavailable — free credits exhausted.",
            "invalid_key": "AI summary unavailable — invalid LLM key.",
        }.get(res.get("error"), f"AI summary unavailable ({res.get('error')}).")
        return {"ok": False, "summary": msg}
    result = {"ok": True, "summary": res["text"], "model": res.get("model")}
    cache.set(cache_key, result, TTL_SUMMARY)
    return result

"""LLM synthesis: gaps + brand context -> content plan (briefs + social + calendar).

Degrades gracefully: if the LLM is unavailable, a deterministic fallback builds
a basic plan straight from the gap topics so the feature still returns value.
"""
import datetime
import json
import math
import re

from services import llm

_SYSTEM = (
    "You are a senior content strategist at a marketing agency. You produce "
    "specific, trend-timed content plans. You ALWAYS reply with strict JSON only "
    "(no markdown, no prose outside the JSON). Match the brand's voice when given. "
    "Never invent statistics."
)


# Bounded so one LLM call completes reliably on the free tier; the calendar
# schedules these across the chosen horizon at the requested cadence.
def _caps(cadence, scope_days):
    weeks = max(1, scope_days / 7)
    apw = cadence.get("articles_per_week", 2)
    spw = cadence.get("social_per_week", 5)
    return min(8, max(4, round(weeks * apw / 2))), min(10, max(6, round(weeks * spw / 3)))


def _prompt(ctx, gaps, n_articles, n_social, platforms):
    gap_lines = "\n".join(
        f"- {g['topic']} (momentum {g['momentum']}/100"
        f"{', BREAKOUT' if g['breakout'] else ''}, "
        f"{g['covered_by']}/{g['competitor_total']} competitors cover it)"
        for g in gaps
    )
    return (
        f"Brand: {ctx.get('niche') or ctx.get('website')}\n"
        f"What they do: {ctx.get('what') or 'n/a'}\n"
        f"Goal: {ctx.get('goal') or 'grow audience'}\n"
        f"Audience: {ctx.get('audience') or 'n/a'}\n"
        f"Brand voice: {ctx.get('voice') or 'professional, clear'}\n"
        f"Region: {ctx.get('geo')}\n\n"
        f"Opportunity topics (gaps vs competitors + trends):\n{gap_lines}\n\n"
        f"Produce a content plan as JSON with this exact shape:\n"
        '{"summary": "2-3 sentences on where they stand and the strategy",'
        ' "articles": [{"title","keyword","angle","why_now",'
        '"format":"guide|listicle|comparison|how-to","outline":["H2","H2","H2"],'
        '"word_target":1500,"include_keywords":["",""],"priority":1}],'
        ' "social": [{"platform","idea","format","topic","why_now"}]}\n\n'
        f"Generate {n_articles} articles (full briefs, outline 3-5 H2s) and "
        f"{n_social} social posts spread across these platforms: {', '.join(platforms)}. "
        f"Tie 'why_now' to the momentum/breakout signal. JSON only."
    )


def _parse_json(text):
    if not text:
        return None
    t = text.strip()
    # Strip markdown code fences the model often wraps JSON in.
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```\s*$", "", t).strip()
    start = t.find("{")
    if start < 0:
        return None
    # Try from the first brace; then first-brace .. last-brace as a fallback.
    for candidate in (t[start:], t[start:t.rfind("}") + 1]):
        try:
            return json.loads(candidate)
        except Exception:  # noqa: BLE001
            continue
    return None


def _dates(n, start, total_days):
    """Spread n items across the horizon, weekdays only."""
    if n <= 0:
        return []
    step = max(1, total_days // n)
    out = []
    d = start
    for _ in range(n):
        while d.weekday() >= 5:  # skip weekend
            d += datetime.timedelta(days=1)
        out.append(d.isoformat())
        d += datetime.timedelta(days=step)
    return out


def _schedule(items, start, total_days):
    dates = _dates(len(items), start, total_days)
    for it, dt in zip(items, dates):
        it["publish_date"] = dt
    return items


def build_plan(ctx, gaps, cadence, platforms, scope_days, footprint_stats):
    n_articles, n_social = _caps(cadence, scope_days)
    platforms = platforms or ["instagram", "linkedin", "x", "tiktok"]

    res = llm.chat(_SYSTEM, _prompt(ctx, gaps, n_articles, n_social, platforms),
                   max_tokens=4500, temperature=0.65, timeout=90)
    plan = _parse_json(res.get("text")) if res.get("ok") else None
    ai = bool(plan)

    if not plan:
        plan = _fallback(ctx, gaps, n_articles, n_social, platforms)

    articles = plan.get("articles", []) or []
    social = plan.get("social", []) or []

    # Attach trend signal from gaps to articles by topic/keyword match.
    gap_by_topic = {g["topic"].lower(): g for g in gaps}
    for a in articles:
        key = (a.get("keyword") or a.get("title") or "").lower()
        match = next((g for t, g in gap_by_topic.items() if t in key or key in t), None)
        if match:
            a["momentum"] = match["momentum"]
            a["breakout"] = match["breakout"]

    today = datetime.date.today()
    _schedule(articles, today, scope_days)
    _schedule(social, today, scope_days)

    return {
        "summary": plan.get("summary", ""),
        "footprint": footprint_stats,
        "articles": articles,
        "social": social,
        "competitor_gaps": [
            {"topic": g["topic"], "covered_by": g["covered_by"],
             "competitor_total": g["competitor_total"], "momentum": g["momentum"],
             "you_cover": False}
            for g in gaps[:10]
        ],
        "ai_generated": ai,
        "scope_days": scope_days,
    }


def _fallback(ctx, gaps, n_articles, n_social, platforms):
    """Deterministic plan from gaps when the LLM is unavailable."""
    fmts = ["guide", "how-to", "listicle", "comparison"]
    articles = []
    for i, g in enumerate(gaps[:n_articles]):
        t = g["topic"]
        articles.append({
            "title": f"The {t.title()} Guide for {ctx.get('niche', 'Your Audience')}",
            "keyword": t, "angle": f"A practical, trend-timed take on {t}.",
            "why_now": ("Breaking now" if g["breakout"] else f"Momentum {g['momentum']}/100")
                       + f"; {g['covered_by']}/{g['competitor_total']} competitors already cover it.",
            "format": fmts[i % len(fmts)],
            "outline": [f"What is {t}", f"Why {t} matters now", f"How to apply {t}"],
            "word_target": 1400, "include_keywords": [t], "priority": i + 1,
        })
    social = []
    for i, g in enumerate(gaps[:n_social]):
        social.append({
            "platform": platforms[i % len(platforms)],
            "idea": f"Quick take on {g['topic']} — why it's heating up.",
            "format": "post", "topic": g["topic"],
            "why_now": "Breaking trend" if g["breakout"] else f"Momentum {g['momentum']}/100",
        })
    return {"summary": f"Based on {len(gaps)} gap topics where competitors and trends "
                       "are ahead, here is a starter plan (generated without the AI model).",
            "articles": articles, "social": social}


def draft(item, voice):
    """On-demand 'Draft this' — expand a brief or social idea into full text."""
    is_article = "outline" in item or "word_target" in item
    if is_article:
        user = (f"Write a complete article.\nTitle: {item.get('title')}\n"
                f"Angle: {item.get('angle')}\nTarget keyword: {item.get('keyword')}\n"
                f"Outline: {item.get('outline')}\nWord target: {item.get('word_target', 1200)}\n"
                f"Brand voice: {voice or 'professional, clear'}\n"
                "Use the outline as H2 sections. Markdown.")
        max_tokens = 1800
    else:
        user = (f"Write a ready-to-post {item.get('platform')} {item.get('format','post')} "
                f"about: {item.get('idea')} (topic: {item.get('topic')}).\n"
                f"Brand voice: {voice or 'professional, clear'}\n"
                "Include a hook and a call to action. Platform-appropriate length.")
        max_tokens = 600
    res = llm.chat("You are an expert copywriter. Write publish-ready content.",
                   user, max_tokens=max_tokens, temperature=0.7, timeout=115)
    if res.get("ok"):
        return {"ok": True, "text": res["text"]}
    return {"ok": False, "text": "Drafting unavailable right now — the AI model is "
            "rate-limited or not configured. Try again shortly."}

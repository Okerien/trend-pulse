"""Gap computation + opportunity scoring.

candidate gaps = (competitor-covered topics ∪ trending topics) − (topics the
brand already covers), ranked by trend momentum × competitor density × recency.

Trend scoring is bounded: we pre-rank candidates cheaply (density + frequency),
keep the top N, and only then hit the trend engine in batches — so pytrends
calls stay small and use the resilience cache.
"""
from services import pytrends_client, metrics, composite
from services.strategy.footprint import topic_set

_SCORE_LIMIT = 12  # how many candidates we spend trend-scoring calls on


def _tokens(phrase):
    return set(phrase.lower().split())


def _covered(phrase, sets):
    """True if `phrase` is already well-covered by any footprint in `sets`."""
    pt = _tokens(phrase)
    if not pt:
        return False
    for s in sets:
        for owned in s:
            ot = _tokens(owned)
            inter = pt & ot
            if inter and len(inter) / len(pt) >= 0.6:
                return True
    return False


def _density(phrase, comp_sets):
    return sum(1 for s in comp_sets if _covered(phrase, [s]))


def compute_gaps(user_fp, competitor_fps, trending_phrases, range_key, geo):
    user_set = topic_set(user_fp)
    comp_sets = [topic_set(fp) for fp in competitor_fps]

    # Build candidate pool: multi-word competitor topics + trending phrases the
    # brand doesn't already cover.
    pool = {}
    for fp in competitor_fps:
        for t in fp.get("topics", []):
            ph = t["phrase"]
            if " " in ph:  # multi-word = more specific/useful
                pool[ph] = pool.get(ph, 0) + t["count"]
    for ph in trending_phrases:
        pool[ph] = pool.get(ph, 0) + 3

    candidates = []
    for ph, freq in pool.items():
        if _covered(ph, [user_set]):
            continue
        candidates.append((ph, freq, _density(ph, comp_sets)))

    # Pre-rank cheaply, then trend-score only the top slice.
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    top = candidates[:_SCORE_LIMIT]
    if not top:
        return []

    phrases = [c[0] for c in top]
    trend = pytrends_client.interest_over_time(phrases, range_key, geo)
    # When Google is throttled, score momentum from Wikipedia instead of zeros.
    if (not trend.get("dates")) or trend.get("demo"):
        comp = composite.interest_from_wikipedia(phrases, range_key)
        if comp and comp.get("dates"):
            trend = comp
    series = trend.get("series", {})

    out = []
    for ph, freq, density in top:
        vals = series.get(ph, [])
        mom = metrics.momentum(vals) if vals else 0
        breakout = metrics.is_breakout(vals) if vals else False
        density_ratio = density / max(1, len(comp_sets))
        opportunity = round(min(100,
            0.5 * mom + 30 * density_ratio + (15 if breakout else 0) + min(10, freq)))
        out.append({
            "topic": ph,
            "momentum": mom,
            "breakout": breakout,
            "covered_by": density,
            "competitor_total": len(comp_sets),
            "opportunity": opportunity,
        })

    out.sort(key=lambda x: x["opportunity"], reverse=True)
    return out

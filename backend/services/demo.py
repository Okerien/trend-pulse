"""Demo / sample-data generator.

Opt-in via env `TRENDPULSE_DEMO=1`. When Google Trends is unavailable
(rate-limited, blocked, offline), endpoints fall back to deterministic
synthetic data so the tool stays presentable in a live client demo.

Every response built here carries `"demo": True` so the frontend can show a
"Sample data" indicator. It never silently masquerades as live data.
"""
import datetime
import hashlib
import math
import random

# (points, step_days) per range — daily for short ranges, weekly for long.
_RANGE = {
    "7D": (7, 1),
    "30D": (30, 1),
    "90D": (90, 1),
    "12M": (52, 7),
    "5Y": (260, 7),
}

_MODIFIERS = ["near me", "online", "price", "2026", "review", "best",
              "trends", "app", "delivery", "vs", "for beginners", "cost"]

_REGIONS = {
    "NG": ["Lagos", "Abuja", "Rivers", "Oyo", "Kano", "Enugu", "Kaduna", "Delta"],
    "ZA": ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State"],
    "US": ["California", "Texas", "New York", "Florida", "Illinois", "Georgia"],
    "GB": ["England", "Scotland", "Wales", "London", "Manchester", "Birmingham"],
    "": ["United States", "India", "Nigeria", "United Kingdom", "Brazil", "Germany"],
}


def _rng(*parts):
    seed = int(hashlib.md5("|".join(parts).lower().encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def _dates(range_key):
    n, step = _RANGE.get(range_key, _RANGE["90D"])
    end = datetime.date.today()
    return [(end - datetime.timedelta(days=(n - 1 - i) * step)).isoformat()
            for i in range(n)]


def series(keyword, range_key):
    """Deterministic, realistic-looking interest series (0-100)."""
    n, _ = _RANGE.get(range_key, _RANGE["90D"])
    r = _rng(keyword, range_key)
    base = r.uniform(28, 52)
    drift = r.uniform(-0.35, 0.75)
    amp = r.uniform(8, 26)
    period = r.choice([7, 14, 30, 90])
    phase = r.uniform(0, 6.28)
    breakout = r.random() < 0.35
    raw = []
    for i in range(n):
        t = i / max(1, n - 1)
        v = (base + drift * 42 * t
             + amp * math.sin(2 * math.pi * i / period + phase)
             + r.uniform(-7, 7))
        if breakout and t > 0.7:
            v += (t - 0.7) * 110
        raw.append(v)
    lo, hi = min(raw), max(raw)
    rng = (hi - lo) or 1
    return [round(max(0, min(100, (v - lo) / rng * 100))) for v in raw]


def trends(keywords, range_key):
    dates = _dates(range_key)
    return {
        "dates": dates,
        "series": {kw: series(kw, range_key) for kw in keywords},
        "stale": False,
        "demo": True,
    }


def related_and_rising(keyword, range_key):
    r = _rng(keyword, "related")
    mods = r.sample(_MODIFIERS, k=min(8, len(_MODIFIERS)))
    related = [{"query": f"{keyword} {m}", "value": r.randint(20, 100)} for m in mods]
    related.sort(key=lambda x: -x["value"])
    rising = [{"query": f"{keyword} {m}",
               "value": r.choice([r.randint(40, 300), r.randint(40, 300), 5000])}
              for m in r.sample(_MODIFIERS, k=5)]
    return {"related": related, "rising": rising, "demo": True}


def interest_by_region(keyword, range_key, region_key):
    names = _REGIONS.get((region_key or "").upper(), _REGIONS[""])
    r = _rng(keyword, "region", region_key or "")
    rows = [{"name": nm, "value": r.randint(25, 100)} for nm in names]
    rows.sort(key=lambda x: -x["value"])
    return rows


def competitors(niche):
    r = _rng(niche or "x", "competitors")
    bases = ["Hub", "Peak", "Vela", "Nova", "Brightly", "Northstar", "Vantage", "Lumen"]
    suffix = r.choice(["", " Labs", " HQ", " Co", " Group"])
    picks = r.sample(bases, 4)
    return [f"{p}{suffix}" for p in picks]


def trending(seed, range_key):
    """Top-10 list for a niche seed."""
    r = _rng(seed, "trending")
    mods = (_MODIFIERS + ["companies", "tools", "ideas", "examples", "jobs", "near me"])
    picks = r.sample(mods, k=10)
    items = [{"query": f"{seed} {m}", "value": r.choice([r.randint(40, 900), 5000])}
             for m in picks]
    items.sort(key=lambda x: -x["value"])
    return items

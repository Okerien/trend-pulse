"""Composite trend signal — a free, reliable fallback for Google Trends.

When pytrends is rate-limited, we derive a real interest series from Wikipedia
daily pageviews (free, unlimited, dependable). Momentum/breakout then compute
from actual data instead of dropping to synthetic demo values.

Priority in the /trends route: pytrends (real) > Wikipedia (real) > demo (synthetic).
"""
from concurrent.futures import ThreadPoolExecutor

from services import enrichers


def interest_from_wikipedia(keywords, range_key):
    """Return {dates, series, source:'wikipedia'} shaped like pytrends output,
    or None if Wikipedia has nothing for any keyword.

    Wikipedia fetches run in parallel — they're independent and the API is fast.
    """
    def fetch(kw):
        w = enrichers.wikipedia_views(kw, range_key) or {}
        return kw, (w.get("series") or [])

    per = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for kw, series in ex.map(fetch, keywords):
            per[kw] = series

    all_dates = sorted({s["date"] for series in per.values() for s in series})
    if not all_dates:
        return None

    dates_iso = [f"{d[:4]}-{d[4:6]}-{d[6:8]}" for d in all_dates]
    series = {}
    for kw, ws in per.items():
        by_date = {s["date"]: s["views"] for s in ws}
        raw = [by_date.get(d) for d in all_dates]
        present = [v for v in raw if v is not None]
        mx = max(present) if present else 1
        # Normalise each keyword to its own peak (0-100), matching the Trends scale.
        series[kw] = [None if v is None else round(v / mx * 100) for v in raw]

    return {"dates": dates_iso, "series": series, "source": "wikipedia", "stale": False}

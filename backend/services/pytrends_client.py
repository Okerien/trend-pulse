"""pytrends wrapper: batching, a 2s inter-batch delay, and graceful failure.

Any upstream failure (Google 429, connection timeout, blocked IP, parse error)
is treated as "temporarily unavailable": we return whatever is cached (if
anything) marked `stale`, so the frontend can show "Data temporarily
unavailable — showing last known values" instead of crashing.
"""
import random
import time

import cache
from config import TIMEFRAME_MAP, GEO_MAP, TTL_TRENDS, DEMO_MODE
from services import demo

_BATCH_SIZE = 5          # pytrends accepts at most 5 keywords per payload
_INTER_BATCH_DELAY = 2   # seconds, to stay under Google's rate limit

# Rotate a small pool of realistic desktop User-Agents so we look less like a bot.
_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def _new_client():
    from pytrends.request import TrendReq
    # Modest retries — when Google throttles we fall back to the Wikipedia
    # composite, so there's no need to burn time retrying aggressively.
    return TrendReq(
        hl="en-US", tz=0, timeout=(8, 18), retries=1, backoff_factor=0.3,
        requests_args={"headers": {"User-Agent": random.choice(_USER_AGENTS)}},
    )


def _timeframe(range_key):
    return TIMEFRAME_MAP.get(range_key, TIMEFRAME_MAP["90D"])


def _geo(region_key):
    return GEO_MAP.get((region_key or "").upper(), "")


class Unavailable(Exception):
    """Raised for any upstream Google Trends failure; triggers cache fallback."""


def interest_over_time(keywords, range_key, region_key):
    """Return {"dates": [iso...], "series": {kw: [int|None]}, "stale": bool}."""
    import pandas as pd

    key = f"trends:{region_key}:{range_key}:{','.join(sorted(keywords))}"
    timeframe = _timeframe(range_key)
    geo = _geo(region_key)

    def produce():
        pytrends = _new_client()
        merged = None
        for i in range(0, len(keywords), _BATCH_SIZE):
            batch = keywords[i:i + _BATCH_SIZE]
            if i > 0:
                time.sleep(_INTER_BATCH_DELAY)
            try:
                pytrends.build_payload(batch, timeframe=timeframe, geo=geo)
                df = pytrends.interest_over_time()
            except Exception:  # noqa: BLE001 — any Google failure -> degrade
                raise Unavailable()
            if df is None or df.empty:
                continue
            if "isPartial" in df.columns:
                # Drop the trailing in-progress period — its value is deflated
                # (often ~0) and would otherwise become a bogus "latest" interest.
                df = df[~df["isPartial"].astype(bool)]
                df = df.drop(columns=["isPartial"])
            merged = df if merged is None else merged.join(df, how="outer")

        if merged is None or merged.empty:
            return {"dates": [], "series": {kw: [] for kw in keywords}, "stale": False}

        merged = merged.sort_index()
        dates = [idx.to_pydatetime().date().isoformat() for idx in merged.index]
        series = {}
        for kw in keywords:
            if kw in merged.columns:
                series[kw] = [None if pd.isna(v) else int(v) for v in merged[kw]]
            else:
                series[kw] = [None] * len(dates)
        return {"dates": dates, "series": series, "stale": False}

    result = _with_fallback(
        key, produce,
        empty={"dates": [], "series": {kw: [] for kw in keywords},
               "stale": True, "error": "unavailable"})
    if DEMO_MODE and not result.get("dates"):
        return demo.trends(keywords, range_key)
    return result


def related_and_rising(keyword, range_key, region_key):
    """Feature 6/7 — related + rising queries for a single keyword."""
    key = f"related:{region_key}:{range_key}:{keyword}"

    def produce():
        pytrends = _new_client()
        try:
            pytrends.build_payload([keyword], timeframe=_timeframe(range_key),
                                   geo=_geo(region_key))
            data = pytrends.related_queries()
        except Exception:  # noqa: BLE001
            raise Unavailable()
        entry = data.get(keyword) or {}
        return {"related": _df_records(entry.get("top")),
                "rising": _df_records(entry.get("rising"))}

    result = _with_fallback(key, produce,
                            empty={"related": [], "rising": [], "stale": True})
    if DEMO_MODE and not result.get("related") and not result.get("rising"):
        return demo.related_and_rising(keyword, range_key)
    return result


def interest_by_region(keyword, range_key, region_key):
    """Feature 6 — regional breakdown for a single keyword."""
    key = f"region:{region_key}:{range_key}:{keyword}"

    def produce():
        pytrends = _new_client()
        resolution = "REGION" if _geo(region_key) else "COUNTRY"
        try:
            pytrends.build_payload([keyword], timeframe=_timeframe(range_key),
                                   geo=_geo(region_key))
            df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True)
        except Exception:  # noqa: BLE001
            raise Unavailable()
        if df is None or df.empty or keyword not in df.columns:
            return []
        df = df.sort_values(keyword, ascending=False).head(15)
        return [{"name": idx, "value": int(val)}
                for idx, val in df[keyword].items() if val and val > 0]

    result = _with_fallback(key, produce, empty=[])
    if DEMO_MODE and not result:
        return demo.interest_by_region(keyword, range_key, region_key)
    return result


def _with_fallback(key, produce, empty):
    """Run producer; cache success; on Unavailable serve recent *real* data from
    the stale window (marked stale) rather than nothing."""
    try:
        return cache.get_or_set(key, TTL_TRENDS, produce)
    except Unavailable:
        cached = cache.get_stale(key)
        if cached is None:
            return empty
        if isinstance(cached, dict):
            stale = dict(cached)
            stale["stale"] = True
            return stale
        return cached


def _df_records(df):
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict("records")

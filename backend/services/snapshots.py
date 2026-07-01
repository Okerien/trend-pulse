"""Persistent trend snapshots — keyword history across sessions.

Each /trends fetch records one data point per keyword per day (latest interest +
momentum) into the persistent cache (Upstash if configured, else SQLite). Over
time this builds a real history that survives sessions — something free,
session-only tools can't do.
"""
import datetime

import cache

_YEAR = 365 * 24 * 60 * 60
_MAX_POINTS = 180


def _key(geo, keyword):
    return f"hist:{(geo or '').upper()}:{keyword.lower().strip()}"


def record(geo, keyword, latest, momentum):
    if latest is None and momentum is None:
        return
    day = datetime.date.today().isoformat()
    key = _key(geo, keyword)
    hist = cache.get_stale(key) or []
    hist = [h for h in hist if h.get("date") != day]  # one point per day
    hist.append({"date": day, "latest": latest, "momentum": momentum})
    hist = hist[-_MAX_POINTS:]
    cache.set(key, hist, ttl=_YEAR, stale_ttl=_YEAR)


def history(geo, keyword):
    return cache.get_stale(_key(geo, keyword)) or []

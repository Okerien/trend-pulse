"""Cache with persistence, serve-stale, and coalescing.

Persistent layer is Upstash Redis (free, survives Render cold starts/redeploys)
when configured, else a local SQLite file (good for dev). In-memory L1 sits in
front of both. Serve-stale keeps recent real data when upstreams fail.
"""
import json
import os
import time
import threading

import sqlite3
import requests

from config import UPSTASH_URL, UPSTASH_TOKEN

_DB_PATH = os.getenv("CACHE_DB", os.path.join(os.path.dirname(__file__), ".cache.sqlite"))
_DEFAULT_STALE_FACTOR = 16
_MIN_STALE = 6 * 60 * 60

_mem = {}
_mem_lock = threading.Lock()
_key_locks = {}
_key_locks_guard = threading.Lock()
_local = threading.local()

_USE_UPSTASH = bool(UPSTASH_URL and UPSTASH_TOKEN)


# ---------- persistent layer ----------
def _conn():
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(_DB_PATH, timeout=5)
        _local.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache "
            "(key TEXT PRIMARY KEY, value TEXT, fresh_until REAL, stale_until REAL)")
        _local.conn.commit()
    return _local.conn


def _upstash(cmd):
    """Run a Redis command via Upstash REST. cmd is a list, e.g. ['GET', key]."""
    r = requests.post(UPSTASH_URL, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
                      json=cmd, timeout=8)
    r.raise_for_status()
    return r.json().get("result")


def _persist_set(key, value, fresh_until, stale_until):
    payload = json.dumps({"v": value, "f": fresh_until, "s": stale_until})
    ttl = max(1, int(stale_until - time.time()))
    if _USE_UPSTASH:
        try:
            _upstash(["SET", key, payload, "EX", ttl])
            return
        except Exception:  # noqa: BLE001 — fall through to sqlite
            pass
    try:
        c = _conn()
        c.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?,?)",
                  (key, payload, fresh_until, stale_until))
        c.commit()
    except Exception:  # noqa: BLE001
        pass


def _persist_get(key):
    """Return (value, fresh_until, stale_until) or None."""
    if _USE_UPSTASH:
        try:
            raw = _upstash(["GET", key])
            if raw:
                d = json.loads(raw)
                return (d["v"], d["f"], d["s"])
        except Exception:  # noqa: BLE001
            pass
        # If Upstash is configured we don't also read sqlite.
        return None
    try:
        row = _conn().execute(
            "SELECT value, fresh_until, stale_until FROM cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        payload, fresh_until, stale_until = row
        d = json.loads(payload)
        return (d["v"], d["f"], d["s"])
    except Exception:  # noqa: BLE001
        return None


def _entry(key):
    with _mem_lock:
        entry = _mem.get(key)
    if entry is not None:
        return entry
    loaded = _persist_get(key)
    if loaded is None:
        return None
    value, fresh_until, stale_until = loaded
    if time.time() > stale_until:
        return None
    entry = (value, fresh_until, stale_until)
    with _mem_lock:
        _mem[key] = entry
    return entry


# ---------- public API ----------
def get(key):
    entry = _entry(key)
    if entry is None:
        return None
    value, fresh_until, _ = entry
    return value if time.time() <= fresh_until else None


def get_stale(key):
    entry = _entry(key)
    if entry is None:
        return None
    value, _, stale_until = entry
    return value if time.time() <= stale_until else None


def set(key, value, ttl, stale_ttl=None):
    now = time.time()
    fresh_until = now + ttl
    stale_until = now + (stale_ttl if stale_ttl else max(ttl * _DEFAULT_STALE_FACTOR, _MIN_STALE))
    with _mem_lock:
        _mem[key] = (value, fresh_until, stale_until)
    _persist_set(key, value, fresh_until, stale_until)


def _lock_for(key):
    with _key_locks_guard:
        lock = _key_locks.get(key)
        if lock is None:
            lock = _key_locks[key] = threading.Lock()
        return lock


def get_or_set(key, ttl, producer):
    cached = get(key)
    if cached is not None:
        return cached
    with _lock_for(key):
        cached = get(key)
        if cached is not None:
            return cached
        value = producer()
        if value is not None:
            set(key, value, ttl)
        return value

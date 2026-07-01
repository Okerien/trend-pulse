"""Shared request-parsing helpers for the route blueprints."""
import datetime

from flask import request

from config import DEFAULT_RANGE, DEFAULT_GEO, TIMEFRAME_MAP, GEO_MAP


def get_keywords():
    """Accept ?keywords=a,b,c  or repeated ?kw=a&kw=b. De-duped, trimmed."""
    raw = request.args.get("keywords")
    if raw:
        items = raw.split(",")
    else:
        items = request.args.getlist("kw")
    seen, out = set(), []
    for it in items:
        kw = it.strip()
        low = kw.lower()
        if kw and low not in seen:
            seen.add(low)
            out.append(kw)
    return out


def get_range():
    r = (request.args.get("range") or DEFAULT_RANGE).upper()
    return r if r in TIMEFRAME_MAP else DEFAULT_RANGE


def get_geo():
    g = (request.args.get("geo") or DEFAULT_GEO).upper()
    return g if g in GEO_MAP else DEFAULT_GEO


def iso_to_dates(iso_list):
    out = []
    for s in iso_list:
        try:
            out.append(datetime.date.fromisoformat(s))
        except (ValueError, TypeError):
            out.append(None)
    return out

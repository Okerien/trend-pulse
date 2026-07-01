"""GET /trends — sparkline data + per-keyword calculated metrics.

Serves Features 1-5, 14, 15, 18, and (when the range carries enough history) 16.
"""
from flask import Blueprint, jsonify, request

import cache
from config import TTL_SEASONAL
from services import pytrends_client, metrics, composite, snapshots
from services.enrichers import currency_rates, news_articles
from routes._helpers import get_keywords, get_range, get_geo, iso_to_dates

bp = Blueprint("trends", __name__)


def _change_pct(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None
    first = next((v for v in vals if v > 0), None)
    if not first:
        return None
    return round((vals[-1] - first) / first * 100)


def _seasonality_for(keyword, geo):
    """Best-effort seasonality using a cached 5-year series (Feature 16)."""
    key = f"seasonal5y:{geo}:{keyword}"
    cached = cache.get(key)
    if cached is not None:
        dates = iso_to_dates(cached["dates"])
        return metrics.detect_seasonality(dates, cached["series"][keyword])
    data = pytrends_client.interest_over_time([keyword], "5Y", geo)
    if data.get("dates"):
        cache.set(key, data, TTL_SEASONAL)
        dates = iso_to_dates(data["dates"])
        return metrics.detect_seasonality(dates, data["series"][keyword])
    return None


@bp.get("/history")
def history():
    """Persistent snapshot history for a keyword (Feature: tracked over time)."""
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"history": []})
    return jsonify({"keyword": keyword, "geo": get_geo(),
                    "history": snapshots.history(get_geo(), keyword)})


@bp.get("/news")
def news():
    """Recent articles for the News drill-down."""
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"articles": []})
    return jsonify({"keyword": keyword, "articles": news_articles(keyword)})


@bp.get("/trends")
def trends():
    keywords = get_keywords()
    range_key = get_range()
    geo = get_geo()
    if not keywords:
        return jsonify({"range": range_key, "geo": geo, "dates": [],
                        "keywords": [], "stale": False})

    data = pytrends_client.interest_over_time(keywords, range_key, geo)
    # Prefer real Wikipedia-derived momentum over synthetic demo data when
    # Google Trends is unavailable. Priority: pytrends > Wikipedia > demo.
    if (not data.get("dates")) or data.get("demo"):
        comp = composite.interest_from_wikipedia(keywords, range_key)
        if comp and comp.get("dates"):
            data = comp

    dates_iso = data.get("dates", [])
    dates = iso_to_dates(dates_iso)

    out = []
    for kw in keywords:
        values = data.get("series", {}).get(kw, [])
        clean = [v for v in values if v is not None]
        score = metrics.momentum(values)
        latest = clean[-1] if clean else None
        out.append({
            "keyword": kw,
            "values": values,
            "latest": latest,
            "peak": max(clean) if clean else None,
            "momentum": score,
            "band": metrics.momentum_band(score),
            "breakout": metrics.is_breakout(values),
            "change_pct": _change_pct(values),
            "best_time": (metrics.best_publish_time(dates, values) or {}).get("sentence"),
            # Seasonality only when the selected range already carries multi-year history.
            "seasonality": (metrics.detect_seasonality(dates, values)
                            if range_key == "5Y" else None),
        })
        # Record a daily history point (persists across sessions).
        try:
            snapshots.record(geo, kw, latest, score)
        except Exception:  # noqa: BLE001
            pass

    return jsonify({
        "range": range_key,
        "geo": geo,
        "dates": dates_iso,
        "keywords": out,
        "fx": currency_rates(),
        "stale": data.get("stale", False),
        "demo": data.get("demo", False),
        "source": data.get("source", "google"),
    })

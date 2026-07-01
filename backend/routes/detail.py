"""GET /detail — deep dive on a single keyword (Features 6, 18; full momentum + 16)."""
import urllib.parse

from flask import Blueprint, jsonify, request

from config import GEO_MAP
from services import pytrends_client, metrics, ai, composite
from routes._helpers import get_range, get_geo, iso_to_dates

bp = Blueprint("detail", __name__)


def _google_trends_url(keyword, range_key, geo):
    tf = {"7D": "now 7-d", "30D": "today 1-m", "90D": "today 3-m",
          "12M": "today 12-m", "5Y": "today 5-y"}.get(range_key, "today 3-m")
    params = {"q": keyword, "date": tf}
    geo_code = GEO_MAP.get(geo, "")
    if geo_code:
        params["geo"] = geo_code
    return "https://trends.google.com/trends/explore?" + urllib.parse.urlencode(params)


@bp.get("/detail")
def detail():
    keyword = (request.args.get("keyword") or "").strip()
    range_key = get_range()
    geo = get_geo()
    if not keyword:
        return jsonify({"error": "missing_keyword"}), 400

    series = pytrends_client.interest_over_time([keyword], range_key, geo)
    dates_iso = series.get("dates", [])
    values = series.get("series", {}).get(keyword, [])
    # Fall back to Wikipedia composite for the chart when Google is throttled.
    if not dates_iso:
        comp = composite.interest_from_wikipedia([keyword], range_key)
        if comp and comp.get("dates"):
            dates_iso = comp["dates"]
            values = comp["series"].get(keyword, [])
    dates = iso_to_dates(dates_iso)

    regions = pytrends_client.interest_by_region(keyword, range_key, geo)
    rq = pytrends_client.related_and_rising(keyword, range_key, geo)

    # AI-suggested related keywords when Google returns nothing.
    ai_related = False
    if not rq.get("related") and not rq.get("rising"):
        sug = ai.suggest_keywords(keyword, 6)
        if sug.get("keywords"):
            rq = {"related": [{"query": k, "value": None} for k in sug["keywords"]],
                  "rising": []}
            ai_related = True

    # Full momentum with regional breadth component.
    regions_above_50 = (sum(1 for r in regions if r["value"] > 50), len(regions)) \
        if regions else None
    score = metrics.momentum(values, regions_above_50)

    return jsonify({
        "keyword": keyword,
        "range": range_key,
        "geo": geo,
        "dates": dates_iso,
        "values": values,
        "momentum": score,
        "band": metrics.momentum_band(score),
        "breakout": metrics.is_breakout(values),
        "seasonality": metrics.detect_seasonality(dates, values),
        "best_time": metrics.best_publish_time(dates, values),
        "related": rq.get("related", []),
        "rising": rq.get("rising", []),
        "regional": regions,
        "ai_related": ai_related,
        "google_trends_url": _google_trends_url(keyword, range_key, geo),
        "stale": series.get("stale", False),
    })

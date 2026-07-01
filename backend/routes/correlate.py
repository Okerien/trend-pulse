"""GET /correlate — Pearson matrix across active keywords (Feature 17).

Fetches the shared time series for the given keywords and computes correlations.
No extra cost beyond the (cached) trends fetch.
"""
from flask import Blueprint, jsonify

from services import pytrends_client
from services.correlation import correlation_matrix
from routes._helpers import get_keywords, get_range, get_geo

bp = Blueprint("correlate", __name__)


@bp.get("/correlate")
def correlate():
    keywords = get_keywords()
    range_key = get_range()
    geo = get_geo()
    if len(keywords) < 2:
        return jsonify({"pairs": []})

    data = pytrends_client.interest_over_time(keywords, range_key, geo)
    series = {kw: [v if v is not None else 0 for v in data["series"].get(kw, [])]
              for kw in keywords}
    return jsonify({"pairs": correlation_matrix(series),
                    "stale": data.get("stale", False)})

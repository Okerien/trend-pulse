"""GET /trending — top trending searches for a niche (Feature 7)."""
from flask import Blueprint, jsonify, request

from config import NICHE_SEEDS, TECH_NICHES
from services import pytrends_client
from routes._helpers import get_range, get_geo

bp = Blueprint("trending", __name__)


@bp.get("/trending")
def trending():
    niche = (request.args.get("niche") or "").lower()
    range_key = get_range()
    geo = get_geo()

    seed = NICHE_SEEDS.get(niche)
    if not seed:
        return jsonify({"niche": niche, "error": "unknown_niche",
                        "items": [], "niches": list(NICHE_SEEDS.keys())})

    data = pytrends_client.related_and_rising(seed, range_key, geo)
    rising = data.get("rising") or []
    related = data.get("related") or []
    source = rising if rising else related

    items = []
    for row in source[:10]:
        items.append({
            "query": row.get("query"),
            "value": row.get("value"),  # rising %: a number; top: 0-100 index
        })

    return jsonify({
        "niche": niche,
        "seed": seed,
        "geo": geo,
        "tech": niche in TECH_NICHES,  # frontend auto-enables GitHub/HN badges
        "items": items,
        "stale": data.get("stale", False),
    })

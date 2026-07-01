"""GET /enrich — batched free-source signals for one keyword (Features 9-13, 21)."""
from flask import Blueprint, jsonify, request

from config import TECH_NICHES
from services import enrichers
from routes._helpers import get_range

bp = Blueprint("enrich", __name__)


def _truthy(name):
    return (request.args.get(name) or "").lower() in ("1", "true", "yes")


@bp.get("/enrich")
def enrich():
    keyword = (request.args.get("keyword") or "").strip()
    range_key = get_range()
    if not keyword:
        return jsonify({"error": "missing_keyword"}), 400

    niche = (request.args.get("niche") or "").lower()
    tech = niche in TECH_NICHES
    include_github = tech or _truthy("github")
    include_hn = tech or _truthy("hn")

    return jsonify(enrichers.enrich(keyword, range_key,
                                    include_github=include_github,
                                    include_hn=include_hn))

"""POST /summarise — AI marketing recommendation (Feature 23).

The frontend POSTs the already-computed data payload (keywords with their
momentum/breakout/seasonality/change/best-time, plus correlations). We accept
GET too, but POST is the real path since the payload is large.
"""
from flask import Blueprint, jsonify, request

from services.llm import summarise as run_summary

bp = Blueprint("summarise", __name__)


@bp.route("/summarise", methods=["POST", "GET"])
def summarise():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
    else:
        # GET fallback: expect a JSON string in ?payload=
        import json
        try:
            payload = json.loads(request.args.get("payload", "{}"))
        except ValueError:
            payload = {}
    if not payload.get("keywords"):
        return jsonify({"ok": False, "summary": "No keyword data provided."}), 400
    return jsonify(run_summary(payload))

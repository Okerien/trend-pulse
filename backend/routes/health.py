from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Render keep-alive ping target."""
    return jsonify({"status": "ok"})

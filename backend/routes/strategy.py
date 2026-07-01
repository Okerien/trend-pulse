"""Content Studio endpoints (Feature: content opportunity engine)."""
from flask import Blueprint, jsonify, request

from services.strategy import orchestrator, providers, synth
from routes._helpers import get_geo

bp = Blueprint("strategy", __name__)


@bp.post("/strategy/analyze")
def analyze():
    body = request.get_json(silent=True) or {}
    if not body.get("website"):
        return jsonify({"error": "missing_website"}), 400
    job_id = orchestrator.start_job(body)
    return jsonify({"job_id": job_id})


@bp.get("/strategy/status")
def status():
    st = orchestrator.status(request.args.get("job_id", ""))
    if st is None:
        return jsonify({"error": "unknown_job"}), 404
    return jsonify(st)


@bp.get("/strategy/result")
def result():
    job_id = request.args.get("job_id", "")
    st = orchestrator.status(job_id)
    if st is None:
        return jsonify({"error": "unknown_job"}), 404
    if not st["done"]:
        return jsonify({"error": "not_ready", "stage": st["stage"]}), 202
    return jsonify(orchestrator.result(job_id))


@bp.get("/strategy/suggest-competitors")
def suggest_competitors():
    website = request.args.get("website", "")
    niche = request.args.get("niche", "")
    if not website and not niche:
        return jsonify({"suggestions": []})
    return jsonify({"suggestions": providers.suggest_competitors(website, niche, "90D", get_geo())})


@bp.post("/strategy/draft")
def draft():
    body = request.get_json(silent=True) or {}
    item = body.get("item")
    if not item:
        return jsonify({"ok": False, "text": "No item to draft."}), 400
    return jsonify(synth.draft(item, body.get("voice", "")))

"""AI intelligence endpoints — Groq reads/suggestions + grounded research."""
from flask import Blueprint, jsonify, request

from services import ai, research
from routes._helpers import get_geo

bp = Blueprint("ai", __name__)


@bp.post("/ai/read")
def read():
    """Per-keyword AI 'read' from its computed signals."""
    kw = request.get_json(silent=True) or {}
    if not kw.get("keyword"):
        return jsonify({"ok": False, "read": ""}), 400
    return jsonify(ai.keyword_read(kw))


@bp.post("/ai/reads")
def reads():
    """Batched per-keyword reads — one Groq call for all (rate-limit safe)."""
    body = request.get_json(silent=True) or {}
    kws = body.get("keywords") or []
    return jsonify(ai.keyword_reads(kws))


@bp.post("/ai/correlate-note")
def correlate_note():
    body = request.get_json(silent=True) or {}
    return jsonify(ai.correlation_note(body.get("pairs") or []))


@bp.get("/ai/suggest")
def suggest():
    seed = request.args.get("seed", "")
    n = min(8, max(3, int(request.args.get("n", 6))))
    return jsonify(ai.suggest_keywords(seed, n))


@bp.get("/ai/niche")
def niche():
    return jsonify(ai.niche_expand(request.args.get("niche", "")))


@bp.post("/ai/ask")
def ask():
    """Grounded, cited answer for the copilot."""
    body = request.get_json(silent=True) or {}
    q = (body.get("question") or "").strip()
    if not q:
        return jsonify({"ok": False, "answer": "Ask a question.", "citations": []}), 400
    ctx = body.get("context")
    if ctx:
        q = f"{q}\n\n(Context — keywords the user is tracking: {ctx})"
    return jsonify(research.grounded_answer(q))


@bp.get("/ai/why")
def why():
    """Grounded 'why is this trending right now' for the detail panel."""
    keyword = (request.args.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"ok": False, "answer": "", "citations": []}), 400
    geo = get_geo()
    region = "" if geo == "GLOBAL" else f" in {geo}"
    return jsonify(research.grounded_answer(
        f"Why is interest in \"{keyword}\" rising or trending right now{region}? "
        f"What recent events, products, or stories are driving it?"))

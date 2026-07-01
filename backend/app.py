"""Trend Pulse backend — Flask app factory.

Run locally:  python app.py
On Render:    gunicorn app:app
"""
import datetime

from flask import Flask, jsonify
from flask_cors import CORS

from config import FRONTEND_ORIGIN
from services.enrichers import currency_rates

from routes.health import bp as health_bp
from routes.trends import bp as trends_bp
from routes.trending import bp as trending_bp
from routes.detail import bp as detail_bp
from routes.enrich import bp as enrich_bp
from routes.correlate import bp as correlate_bp
from routes.summarise import bp as summarise_bp
from routes.strategy import bp as strategy_bp
from routes.ai import bp as ai_bp


def create_app():
    app = Flask(__name__)

    origins = "*" if FRONTEND_ORIGIN == "*" else [
        o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip()
    ]
    CORS(app, resources={r"/*": {"origins": origins}})

    for bp in (health_bp, trends_bp, trending_bp, detail_bp,
               enrich_bp, correlate_bp, summarise_bp, strategy_bp, ai_bp):
        app.register_blueprint(bp)

    @app.get("/")
    def index():
        return jsonify({"service": "trend-pulse", "status": "ok",
                        "endpoints": ["/health", "/trends", "/trending", "/detail",
                                      "/enrich", "/correlate", "/summarise", "/context"]})

    @app.get("/context")
    def context():
        """Feature 22 — currency strip + last-refreshed timestamp."""
        return jsonify({
            "fx": currency_rates(),
            "refreshed_at": datetime.datetime.utcnow().isoformat() + "Z",
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

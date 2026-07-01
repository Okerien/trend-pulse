# Trend Pulse

A Google Trends intelligence platform for BendingWaters. Flask backend + React (Vite) frontend, enriched with five free data sources, calculated momentum/seasonality/correlation metrics, and AI-generated marketing recommendations. **$0 recurring cost.**

See [BUILD_PLAN.md](BUILD_PLAN.md) for the full architecture and feature map.

## Repo layout

```
backend/    Flask API  -> Render
frontend/   Vite/React -> Vercel   (built in a later phase)
```

## Backend — local dev

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # Render uses Python 3.11
cp .env.example .env                      # then paste your keys
python app.py                             # http://localhost:5000
```

Smoke-test:
```bash
curl localhost:5000/health
curl "localhost:5000/trends?keywords=jollof%20rice,suya&range=90D&geo=NG"
```

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/health`    | keep-alive ping |
| GET  | `/trends`    | sparkline data + momentum/breakout/best-time per keyword |
| GET  | `/trending`  | top-10 trending searches for a niche |
| GET  | `/detail`    | related/rising/regional + full momentum + seasonality |
| GET  | `/enrich`    | Wikipedia / Reddit / HN / news / YouTube / GitHub counts |
| GET  | `/correlate` | Pearson matrix across keywords |
| POST | `/summarise` | AI marketing recommendation (Mistral via Hugging Face) |
| GET  | `/context`   | currency strip + last-refreshed timestamp |

### Live-data reliability

Google Trends has no official API; `pytrends` scrapes it and Google rate-limits scrapers (more so from cloud IPs like Render). The backend mitigates this for free:

- **Persistent cache** (`backend/.cache.sqlite`) — real data survives restarts / cold starts.
- **Serve-stale** — when Google rate-limits, recent *real* data is served (flagged stale) instead of nothing.
- **Request coalescing** — concurrent identical fetches run once.
- **Backoff + jitter + rotating User-Agents** on pytrends requests.
- **Demo fallback** — only when there is no real/stale data, and only if `TRENDPULSE_DEMO=1`; always flagged "Sample data" in the UI.

This makes live data reliable *most* of the time at $0. For guaranteed live data, route pytrends through a residential proxy or add a paid Trends API (SerpAPI / DataForSEO) as a fallback.

### Keys

Only 4 of 23 features need keys (Hugging Face, GNews, YouTube, GitHub). Put them in `backend/.env` — see `.env.example`. Every other feature works with no keys. A missing key just hides that one signal.

## Deploy

Backend → Render via `backend/render.yaml` (Blueprint). Frontend → Vercel. Keep-alive: cron-job.org pings `/health` every 10 min. Full steps land with the frontend phase.

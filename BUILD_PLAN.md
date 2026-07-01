# Trend Pulse — Repo & File-by-File Build Plan

> Status: **planning only, no code yet.** Frontend stack decided: **Vite + React** (not CRA).
> Review this, then say "build it" (or "build the backend") to start Phase 1.

---

## 1. Repository layout

```
trend-pulse/
├── README.md                  # setup + 45-min deploy guide
├── .gitignore                 # node_modules, .env, __pycache__, dist
│
├── backend/                   # Flask API → Render
│   ├── app.py                 # entrypoint, CORS, route registration
│   ├── config.py              # env loading, constants, cache TTLs
│   ├── cache.py               # in-memory dict TTL cache (no Redis)
│   ├── requirements.txt
│   ├── render.yaml            # Render Blueprint (generated via render-deploy skill)
│   ├── .env.example           # documents every key, no secrets
│   ├── routes/
│   │   ├── trends.py          # GET /trends      (pytrends sparkline data)
│   │   ├── trending.py        # GET /trending    (niche top-10)
│   │   ├── detail.py          # GET /detail      (related/rising/regional/best-time)
│   │   ├── enrich.py          # GET /enrich      (wiki/reddit/hn/news/youtube/github)
│   │   ├── correlate.py       # GET /correlate   (Pearson matrix)
│   │   ├── summarise.py       # GET /summarise   (HF Mistral)
│   │   └── health.py          # GET /health      (keep-alive ping)
│   └── services/
│       ├── pytrends_client.py # queue + 2s delay + 429→cache fallback
│       ├── enrichers.py       # one fn per free API
│       ├── metrics.py         # momentum, breakout, seasonality, best-time
│       ├── correlation.py     # Pearson over shared series
│       └── llm.py             # Hugging Face Inference call + prompt
│
└── frontend/                  # Vite + React → Vercel
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example           # VITE_API_URL
    └── src/
        ├── main.jsx
        ├── App.jsx            # mode router (Tracker / Niche / Report)
        ├── context/
        │   └── AppContext.jsx # keywords, range, geo, colors, URL sync
        ├── lib/
        │   ├── api.js         # fetch wrappers for the 7 endpoints
        │   ├── colors.js      # 12-color colorblind-safe palette
        │   ├── urlState.js    # encode/decode share + report URLs
        │   ├── exportPng.js   # html2canvas → white-bg PNG
        │   └── exportCsv.js   # CSV serialiser
        ├── components/
        │   ├── TopBar.jsx          # currency strip, region, range, report toggle
        │   ├── KeywordInput.jsx    # search + HN/Reddit autocomplete
        │   ├── KeywordGrid.jsx
        │   ├── KeywordCard.jsx     # sparkline, momentum, badges, enrich, bookmark
        │   ├── ComparisonChart.jsx
        │   ├── CorrelationMatrix.jsx
        │   ├── NicheExplorer.jsx
        │   ├── DetailPanel.jsx
        │   ├── WatchlistPanel.jsx
        │   ├── InsightPanel.jsx
        │   └── ReportView.jsx
        └── styles/
            └── global.css     # custom CSS only, target <200kb bundle
```

---

## 2. Backend — what each file does

| File | Responsibility | Features served |
|---|---|---|
| `app.py` | Flask app, CORS for the Vercel origin, register all routes | — |
| `config.py` | Load `.env`, hold cache TTLs (Trends 15m, Wiki 60m, social 30m, FX 5m, summary 60m), niche→category map, region list | 4, 5, 7 |
| `cache.py` | `get(key)` / `set(key, val, ttl)` dict cache with timestamp expiry | all (perf) |
| `routes/trends.py` | keywords+timeframe+geo → per-keyword time series | 1, 2, 3, 4, 5 |
| `routes/trending.py` | geo+category → top-10 trending | 7 |
| `routes/detail.py` | one keyword → related, rising, regional, best-publish-time | 6, 18 |
| `routes/enrich.py` | one keyword → wiki/reddit/news/youtube/hn/github counts (batched) | 9–13, 21 |
| `routes/correlate.py` | many keywords → Pearson matrix | 17 |
| `routes/summarise.py` | data payload → HF Mistral 3-sentence recommendation | 23 |
| `routes/health.py` | `{"status":"ok"}` | keep-alive |
| `services/pytrends_client.py` | batching, 2s delay, 429→serve cache or graceful error | rate-limit safety |
| `services/enrichers.py` | Wikimedia, Reddit JSON, HN Algolia, GNews, YouTube, GitHub, Frankfurter | 9–13, 21, 22 |
| `services/metrics.py` | momentum 0–100, breakout flag, seasonality (5y compare), best-time | 14, 15, 16, 18 |
| `services/correlation.py` | Pearson coefficients | 17 |
| `services/llm.py` | HF Inference request + prompt template | 23 |

**Calculated features need no external API:** momentum (14), breakout (15), seasonality (16), correlation (17), best-time (18) — all derived from the pytrends series already fetched.

`requirements.txt`: `flask`, `flask-cors`, `pytrends`, `requests`, `python-dotenv`, `numpy` (for Pearson/slope), `gunicorn` (Render runtime).

---

## 3. Frontend — what each file does

| File | Responsibility | Features |
|---|---|---|
| `AppContext.jsx` | Global state: active keywords+colors, range, geo, report flag; keeps URL in sync | 1, 4, 5, 19 |
| `lib/colors.js` | 12 distinct colorblind-safe colors, persistent assignment | 1 |
| `lib/urlState.js` | One encoder/decoder powering BOTH share links and `/report?client=...` | 8, 19 |
| `lib/exportPng.js` / `exportCsv.js` | PNG + CSV export | 8 |
| `TopBar.jsx` | currency strip (FX), region dropdown, range pills (7D/30D/90D/12M/5Y), report toggle | 4, 5, 19, 22 |
| `KeywordInput.jsx` | add keyword + autocomplete from HN/Reddit trending | 1 |
| `KeywordCard.jsx` | animated sparkline, live + momentum score, breakout/seasonal pills, enrich badges, Wiki-overlay switch, bookmark | 1, 2, 9–16, 20, 21 |
| `ComparisonChart.jsx` | overlay all keywords, multi-line hover, "Generate insight" button | 3, 23 |
| `CorrelationMatrix.jsx` | pairwise matrix when 2+ keywords active | 17 |
| `NicheExplorer.jsx` | 8 niches → top-10 → one-click add + refresh | 7 |
| `DetailPanel.jsx` | slide-in: hi-res chart, related/rising, regional, best-time, Google Trends deep link | 6, 18 |
| `WatchlistPanel.jsx` | localStorage pins + notes + momentum/breakout | 20 |
| `InsightPanel.jsx` | renders AI summary | 23 |
| `ReportView.jsx` | chrome-hidden client view, client name from URL | 19 |

Charts: **Recharts**. Export: **html2canvas** + custom CSV. State: **React Context**. CSS: custom only.

---

## 4. Environment variables

**Backend `.env`** (4 key-gated features; the other 19 work with no keys):
```
HUGGINGFACE_API_TOKEN=     # Feature 23 — AI summary
GNEWS_API_KEY=             # Feature 11 — news count
YOUTUBE_API_KEY=           # Feature 12 — video count
GITHUB_TOKEN=              # Feature 13 — repo count
FRONTEND_ORIGIN=           # CORS allowlist (Vercel URL)
```
**Frontend `.env`:**
```
VITE_API_URL=              # Render backend URL
```
Every key gates exactly one feature — missing key → that badge hides, rest of the app is unaffected.

---

## 5. Build phases (once approved)

1. **Backend skeleton** — Flask, CORS, 7 stubbed endpoints, cache layer, `/health`.
2. **pytrends live** — real `/trends` with 2s queue + 429 fallback.
3. **🎓 Teach-point #1 (learn skill):** momentum / breakout / seasonality / correlation math — so you can defend a green-vs-amber score in a client meeting.
4. **Enrichers + `/correlate` + `/summarise`.**
5. **Frontend skeleton** — Vite, Context, component tree, URL state.
6. **Wire Mode 1 (Tracker)** — cards, sparklines, comparison chart, badges, switchers, detail panel, exports.
7. **Wire Mode 2 (Niche Explorer).**
8. **Enrichment overlays, correlation matrix, currency strip, watchlist, insight panel, report mode.**
9. **🎓 Teach-point #2 (learn skill):** state ↔ URL ↔ localStorage flow — so you can debug a broken share/report link yourself.
10. **Local verification** — every feature + graceful degradation.
11. **Deploy (render-deploy skill)** — GitHub → Render (backend) → Vercel (frontend) → cron-job.org keep-alive → optional CNAME.

---

## 6. What I need from you (only blocks 4 of 23 features)

- Hugging Face token, GNews key, YouTube key, GitHub token → paste into backend `.env`
- Render, Vercel, cron-job.org accounts (for Phase 11)

Everything else — all pytrends data, Wikipedia, Reddit, HN, currency, and every calculated metric — runs with zero keys from day one.

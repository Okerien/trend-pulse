# Content Studio — feature design (v1)

> A third mode in Trend Pulse. Intake a brand → analyze their footprint vs competitors and trends → produce a ranked content plan (articles + social). Differentiator: **trend timing** layered on gap analysis.
>
> Decisions locked: **free now, paid-ready architecture** · **competitors = user-listed + our suggestions** · **balanced articles + social**.
>
> Round 2/3 locked: **rich intake, frictional fields optional + "more detail = better results" nudge** · **brand voice captured & matched** · **90-day calendar with 30-day toggle + ranked backlog** · **user-set cadence sliders (articles/wk + social/wk)** · **content briefs by default + on-demand "Draft this" full-text** · **platforms: Instagram, LinkedIn, X, TikTok** · **plans saved per client (localStorage)**.

---

## 1. User flow

```
Intake wizard (short)  →  "Analyzing…" progress  →  Content Plan dashboard
```

**Intake — rich form, but only 3 required; frictional fields optional with a "the more you share, the sharper your plan" nudge:**
1. Website URL  *(required)*
2. What do you do? — one line  *(required; also auto-confirmed from the crawl)*
3. Primary market — region dropdown (reuse existing)  *(required)*
4. Goal — chips: Brand awareness · Leads & conversions · SEO authority · Social growth  *(optional)*
5. Competitors — up to 3 URLs *(optional)* + "suggest some for me"
6. Socials — handles + priority platforms *(optional)*
7. Target audience — one line  *(optional)*
8. Brand voice — a sentence or paste a paragraph of their copy  *(optional; we also infer voice from the crawl)*
9. Cadence sliders — articles/week + social posts/week  *(optional; defaults to ~2 + ~5)*

**Progress states (real, not fake):** Crawling your site → Reading competitors → Scoring trends → Writing your plan. Each lights up as the backend completes that stage.

**Output dashboard:**
- **Where you stand** — short narrative + footprint stats (topics you cover, competitors' coverage, your gaps).
- **Opportunity map** — ranked gap topics as cards: topic, momentum score, breakout/seasonal badge, "N of 3 competitors cover this", "you don't".
- **Content calendar** — 90-day plan with publish dates honoring the cadence; **toggle to a 30-day focused view**. Backlog/list view alongside.
- **Article plan** — content-brief cards: title, target keyword, angle, *why now* (trend signal), suggested outline (H2s), word-count target, keywords to include, priority. **"Draft this"** button expands any brief into full article text on demand. Export CSV / copy.
- **Social plan** — cards per platform (IG / LinkedIn / X / TikTok): hook/idea, format (reel/carousel/post/thread), tied topic, why now. "Draft this" available.
- **Competitor view** — what the leaders publish that you don't.
- **Saved plans** — generated plans persist per client (localStorage); revisit / compare / re-run.

---

## 2. Pipeline

```
INTAKE → CRAWL → TREND OVERLAY → GAP SCORING → AI SYNTHESIS → PLAN
```

1. **Crawl** (free): robots.txt-respecting fetch of sitemap + top ~40 pages of the user's site and each competitor. Extract title, meta, H1/H2, lead paragraph → a **topic footprint** per domain.
2. **Competitor suggestions** (free heuristic): pull the brand's pytrends *related queries* — competitor names frequently surface there (esp. "brand vs X"). Suggest those + niche leaders. (Paid discovery is a later drop-in.)
3. **Trend overlay**: take candidate topics (competitor-covered ∪ niche-trending ∪ rising queries), cap to ~20, score each with the existing engine (momentum / breakout / seasonality) for the region. Uses the resilience cache so we don't hammer Google.
4. **Gap scoring**: `candidates = (competitorTopics ∪ trendingTopics) − userTopics`, ranked by `momentum × competitorDensity × userAbsence`, with a seasonal penalty when the goal is evergreen authority.
5. **AI synthesis** (Llama via existing LLM service): compact structured JSON in → content plan JSON out (schema in §4). We send *extracted* data, never raw pages (token budget).

---

## 3. Architecture — paid-ready from day one

A provider interface so paid data drops in later with no rework:

```
backend/services/strategy/
  orchestrator.py     # runs the pipeline, owns the job lifecycle
  crawl.py            # FREE: requests + BeautifulSoup; polite, capped
  footprint.py        # topic extraction + light clustering
  competitors.py      # FREE: related-query heuristic suggestions
  gaps.py             # gap computation + opportunity scoring
  synth.py            # builds the LLM prompt, parses the plan JSON
  providers.py        # interfaces: CrawlProvider, SocialProvider, SerpProvider
```

`providers.py` defines interfaces; v1 ships free implementations. Later, a `BrightDataSocialProvider` / `SerpApiProvider` implements the same interface and is selected by env — the orchestrator never changes. **This is what "paid-ready" means.**

**New dependency:** `beautifulsoup4` (lxml already present).

---

## 4. Backend endpoints (job model)

Crawling several sites + trend scoring takes 30-90s — too long for one request on Render's free tier. So a small **job model** (in-memory, fits free tier):

| Method | Path | Purpose |
|---|---|---|
| POST | `/strategy/analyze` | body: website, competitors[], niche, geo, goal, socials → returns `{job_id}` |
| GET  | `/strategy/status?job_id=` | `{stage, progress, partial?}` for the progress UI |
| GET  | `/strategy/result?job_id=` | final content-plan JSON when stage = done |
| GET  | `/strategy/suggest-competitors?website=&niche=` | quick competitor suggestions for the intake step |
| POST | `/strategy/draft` | body: a brief or social idea + brand voice → full draft text (on-demand "Draft this") |

**Plan JSON (LLM output, parsed + validated):**
```json
{
  "summary": "where you stand, 2-3 sentences",
  "footprint": { "you": 42, "competitors_cover": 88, "your_gaps": 31 },
  "articles": [
    { "title": "...", "keyword": "...", "angle": "...", "why_now": "...",
      "format": "guide|listicle|comparison|how-to", "priority": 1,
      "momentum": 78, "breakout": true,
      "outline": ["H2 ...", "H2 ..."], "word_target": 1500,
      "include_keywords": ["...", "..."], "publish_date": "2026-07-08" }
  ],
  "social": [
    { "platform": "instagram|x|linkedin|tiktok", "idea": "...",
      "format": "reel|carousel|post|thread", "topic": "...", "why_now": "...",
      "publish_date": "2026-07-03" }
  ],
  "competitor_gaps": [
    { "topic": "...", "covered_by": 3, "you_cover": false, "momentum": 81 }
  ]
}
```

---

## 5. Honest limits (set client expectations)

- **No real SERP/backlink rankings on free.** We show content-footprint + trend trajectory ("what leaders publish that you don't, and which of it is trending"), not literal Google positions. Real rankings = paid Tier-2.
- **No deep IG analysis on free.** Handles tailor recommendations; real social mining = paid Tier-2 (BrightData/Nimble) or the brand connecting their own IG.
- **Some sites block crawlers** (403). We degrade gracefully and tell the user which sites we couldn't read.
- **Llama-8B is good, not expert.** Strong with structured input + tight prompting; a better model would lift strategy quality.
- **pytrends rate limits** apply here too — topic scoring is capped and uses the resilience cache; falls back to recent/sample signals.

---

## 6. Build phases (when approved)

1. Backend: crawl + footprint extraction (+ `beautifulsoup4`), test on real sites.
2. Backend: competitor suggestions + trend overlay + gap scoring.
3. Backend: LLM synthesis + the 4 endpoints + job model.
4. Frontend: intake wizard + progress UI.
5. Frontend: Content Plan dashboard (opportunity map, article plan, social plan, competitor view) + export.
6. Local verification end-to-end on a real brand + competitors.

---

## 7. Open calls I've made (flag if you disagree)
- **Job/polling model** over a single long request (avoids Render timeouts, enables real progress UI).
- **Third mode** "Content Studio" tab, not a separate app.
- **Crawl cap ~40 pages/site, ~20 scored topics** for v1 (speed + rate-limit safety); tunable.
- Competitor *suggestions* on free are heuristic (related-query based) and modest; real discovery is a paid upgrade.

"""Job orchestrator for the content-plan pipeline.

Crawling several sites + trend scoring + LLM is 30-90s — too long for one HTTP
request on Render's free tier. So we run it on a background thread and expose
job status/result for the frontend to poll, which also powers the progress UI.

In-memory job store (fits the free tier; lost on restart, which is fine for a
generate-then-export flow).
"""
import threading
import time
import uuid

from services import pytrends_client
from services.strategy import providers, footprint, gaps, synth

_jobs = {}
_lock = threading.Lock()

_STAGES = [
    ("crawling_site", "Crawling your site", 10),
    ("reading_competitors", "Reading competitors", 35),
    ("scoring_trends", "Scoring trends", 65),
    ("writing_plan", "Writing your plan", 85),
    ("done", "Done", 100),
]
_PCT = {s[0]: s[2] for s in _STAGES}
_LABEL = {s[0]: s[1] for s in _STAGES}


def _set(job_id, **kw):
    with _lock:
        _jobs.get(job_id, {}).update(kw)


def start_job(params):
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {"stage": "queued", "label": "Queued", "progress": 3,
                         "result": None, "error": None, "created": time.time()}
    threading.Thread(target=_run, args=(job_id, params), daemon=True).start()
    return job_id


def status(job_id):
    with _lock:
        j = _jobs.get(job_id)
        if not j:
            return None
        return {"stage": j["stage"], "label": j["label"], "progress": j["progress"],
                "error": j["error"], "done": j["stage"] == "done"}


def result(job_id):
    with _lock:
        j = _jobs.get(job_id)
        return j["result"] if j else None


def _stage(job_id, key):
    _set(job_id, stage=key, label=_LABEL[key], progress=_PCT[key])


def _run(job_id, params):
    try:
        website = params["website"]
        geo = params.get("geo", "NG")
        range_key = params.get("range", "90D")
        niche = params.get("what") or params.get("niche") or ""
        competitor_urls = [u for u in params.get("competitors", []) if u][:3]

        # 1. Crawl the brand's own site.
        _stage(job_id, "crawling_site")
        user_crawl = providers.crawl_site(website, max_pages=10, time_budget=16)
        user_fp = footprint.extract_topics(user_crawl)
        # Infer a light voice hint from their own titles if none provided.
        voice = params.get("voice") or ""
        if not voice and user_fp["titles"]:
            voice = "tone consistent with: " + "; ".join(user_fp["titles"][:3])

        # 2. Competitors: user-provided, plus auto-discovered (Brave) if none given.
        _stage(job_id, "reading_competitors")
        if not competitor_urls and niche:
            discovered = providers.suggest_competitors(website, niche, range_key, geo, 3)
            competitor_urls = [d["url"] for d in discovered if d.get("url")][:3]

        # Competitors need mainly sitemap-slug breadth, not many page fetches — keep fast.
        competitor_fps, unreadable = [], []
        for cu in competitor_urls:
            c = providers.crawl_site(cu, max_pages=4, time_budget=9)
            if not (c.get("pages") or c.get("urls")):
                c = providers.crawl_site(cu, max_pages=4, time_budget=9)  # one retry
            if c.get("pages") or c.get("urls"):
                competitor_fps.append(footprint.extract_topics(c))
            else:
                unreadable.append(cu)

        # 3. Trending phrases for the niche + gap scoring.
        _stage(job_id, "scoring_trends")
        trending_phrases = []
        if niche:
            rq = pytrends_client.related_and_rising(niche, range_key, geo)
            trending_phrases = [r["query"] for r in (rq.get("rising", []) + rq.get("related", []))
                                if r.get("query")][:10]
        gap_list = gaps.compute_gaps(user_fp, competitor_fps, trending_phrases, range_key, geo)

        # 4. Synthesize the plan.
        _stage(job_id, "writing_plan")
        ctx = {"website": website, "niche": niche, "what": params.get("what"),
               "goal": params.get("goal"), "audience": params.get("audience"),
               "voice": voice, "geo": geo}
        cadence = params.get("cadence", {"articles_per_week": 2, "social_per_week": 5})
        platforms = params.get("platforms", ["instagram", "linkedin", "x", "tiktok"])
        scope_days = int(params.get("scope_days", 90))
        footprint_stats = {
            "you": len(user_fp["topics"]),
            "competitors_cover": len({t["phrase"] for fp in competitor_fps for t in fp["topics"]}),
            "your_gaps": len(gap_list),
        }
        plan = synth.build_plan(ctx, gap_list, cadence, platforms, scope_days, footprint_stats)

        plan["meta"] = {
            "website": website, "geo": geo, "scope_days": scope_days,
            "competitors_read": len(competitor_fps),
            "competitors_unreadable": unreadable,
            "user_pages_read": user_fp["page_count"],
            "stale": user_crawl.get("error") == "no_pages",
        }
        _set(job_id, result=plan)
        _stage(job_id, "done")
    except Exception as exc:  # noqa: BLE001
        _set(job_id, stage="error", label="Failed", error=type(exc).__name__)

"""Brave Search API (free 2k/mo) — real SERP results for competitor discovery
and ranking signal. Returns actual ranking domains, not guessed names.
"""
import re
import urllib.parse

import requests

import cache
from config import BRAVE_API_KEY

_URL = "https://api.search.brave.com/res/v1/web/search"
_TTL = 6 * 60 * 60

# Domains that rank for everything — not competitors.
_GENERIC = {
    "wikipedia.org", "youtube.com", "reddit.com", "linkedin.com", "facebook.com",
    "instagram.com", "twitter.com", "x.com", "amazon.com", "medium.com",
    "quora.com", "pinterest.com", "tiktok.com", "g2.com", "capterra.com",
    "forbes.com", "techcrunch.com", "github.com", "apple.com", "play.google.com",
}


def available():
    return bool(BRAVE_API_KEY)


def search(query, count=10):
    """Return [{title, url, description}] from Brave web search."""
    key = f"brave:{query}:{count}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    def produce():
        try:
            r = requests.get(_URL, headers={"X-Subscription-Token": BRAVE_API_KEY,
                                            "Accept": "application/json"},
                             params={"q": query, "count": count}, timeout=12)
            if r.status_code != 200:
                return []
            results = r.json().get("web", {}).get("results", [])
            return [{"title": x.get("title", ""), "url": x.get("url", ""),
                     "description": x.get("description", "")} for x in results]
        except Exception:  # noqa: BLE001
            return []

    return cache.get_or_set(key, _TTL, produce)


def _root_domain(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    host = re.sub(r"^www\.", "", host)
    return host


def discover_competitors(niche, brand_url="", limit=5):
    """Real competitor discovery: who ranks for the niche's commercial queries."""
    brand_domain = _root_domain(brand_url) if brand_url else ""
    queries = [f"best {niche} tools", f"top {niche} companies", f"{niche} software"]
    scored = {}
    for q in queries:
        for rank, res in enumerate(search(q, 10)):
            dom = _root_domain(res["url"])
            if not dom or dom == brand_domain:
                continue
            if any(dom == g or dom.endswith("." + g) for g in _GENERIC):
                continue
            # Earlier ranks + appearing across queries = stronger competitor.
            scored[dom] = scored.get(dom, 0) + (10 - rank)
    ranked = sorted(scored.items(), key=lambda x: -x[1])
    return [{"name": d, "url": f"https://{d}", "source": "brave", "serp_score": s}
            for d, s in ranked[:limit]]

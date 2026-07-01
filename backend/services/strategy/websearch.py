"""Web search for competitor discovery — keyless by default.

Backend priority:
  1. Brave Search API  (if BRAVE_API_KEY set — best quality, needs key+card)
  2. DuckDuckGo HTML    (no key, no card — works immediately)

Both return [{title, url, description}]. Discovery logic is backend-agnostic.
"""
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

import cache
from services.strategy import brave

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_TTL = 6 * 60 * 60

_root_domain = brave._root_domain
# Generic + review/aggregator/listicle domains that rank for "best X" but aren't competitors.
_GENERIC = brave._GENERIC | {
    "softwareadvice.com", "softwaretestinghelp.com", "getapp.com", "trustradius.com",
    "pcmag.com", "cnet.com", "businessnewsdaily.com", "thecmo.com", "zapier.com",
    "influencermarketinghub.com", "techradar.com", "gartner.com", "trustpilot.com",
    "producthunt.com", "slant.co", "saashub.com", "sourceforge.net", "crozdesk.com",
    "wikipedia.org", "youtube.com", "nerdwallet.com", "investopedia.com",
    "guideflow.com", "worldmetrics.org", "project-management.com", "techrepublic.com",
    "thedigitalprojectmanager.com", "workflowautomation.net", "expertmarket.com",
    "tech.co", "selecthub.com", "financesonline.com", "alternativeto.net",
    "bloggingwizard.com", "emailvendorselection.com", "theguidex.com",
    "thebusinessdive.com", "cybernews.com", "websiteplanet.com",
}


def _norm(url):
    return url if "://" in (url or "") else "https://" + (url or "")


def _brand_token(url):
    host = _root_domain(_norm(url))
    return host.split(".")[0].replace("-", " ") if host else ""


def usable():
    return True  # DuckDuckGo needs no key, so search is always available.


def _ddg(query, count):
    key = f"ddg:{query}:{count}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    def produce():
        try:
            r = requests.post("https://html.duckduckgo.com/html/",
                              data={"q": query}, headers={"User-Agent": _UA}, timeout=12)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            out = []
            for res in soup.select("div.result")[:count]:
                a = res.select_one("a.result__a")
                if not a:
                    continue
                url = _unwrap(a.get("href", ""))
                if not url:
                    continue
                snip = res.select_one(".result__snippet")
                out.append({"title": a.get_text(" ", strip=True), "url": url,
                            "description": snip.get_text(" ", strip=True) if snip else ""})
            if not out:  # layout fallback
                for a in soup.select("a.result__a")[:count]:
                    url = _unwrap(a.get("href", ""))
                    if url:
                        out.append({"title": a.get_text(" ", strip=True), "url": url, "description": ""})
            return out
        except Exception:  # noqa: BLE001
            return []

    return cache.get_or_set(key, _TTL, produce)


def _unwrap(href):
    """DDG wraps links as //duckduckgo.com/l/?uddg=<encoded-url>&..."""
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    parsed = urllib.parse.urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = urllib.parse.parse_qs(parsed.query)
        return urllib.parse.unquote(qs.get("uddg", [""])[0])
    return href


def search(query, count=10):
    if brave.available():
        res = brave.search(query, count)
        if res:
            return res
    return _ddg(query, count)


def discover_competitors(niche, brand_url="", limit=5):
    """Who ranks for the niche's commercial queries = real competitors (with URLs).

    Brand-'alternatives'/'vs' queries surface actual products best; niche queries
    add breadth. Review/aggregator domains are filtered out.
    """
    brand_domain = _root_domain(_norm(brand_url)) if brand_url else ""
    brand = _brand_token(brand_url)
    queries = []
    if brand:
        queries += [f"{brand} alternatives", f"{brand} vs", f"{brand} competitors"]
    queries += [f"{niche}", f"best {niche} tools"]

    scored = {}
    for q in queries:
        # Brand-specific queries are stronger signal — weight them higher.
        weight = 1.5 if brand and brand in q else 1.0
        for rank, res in enumerate(search(q, 10)):
            dom = _root_domain(res.get("url", ""))
            if not dom or dom == brand_domain:
                continue
            if any(dom == g or dom.endswith("." + g) for g in _GENERIC):
                continue
            scored[dom] = scored.get(dom, 0) + (10 - rank) * weight
    ranked = sorted(scored.items(), key=lambda x: -x[1])
    src = "brave" if brave.available() else "duckduckgo"
    return [{"name": d, "url": f"https://{d}", "source": src, "serp_score": round(s)}
            for d, s in ranked[:limit]]

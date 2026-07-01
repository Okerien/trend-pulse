"""Free data-source enrichers (Features 9-13, 21, 22).

Every function fails soft: on any error it returns None / 0 / [] so a single
flaky source never breaks the response. Each is individually cached.
"""
import datetime
import urllib.parse

import requests

import cache
from config import (GNEWS_API_KEY, YOUTUBE_API_KEY, GITHUB_TOKEN,
                    TTL_WIKI, TTL_SOCIAL, TTL_CURRENCY)

_UA = {"User-Agent": "TrendPulse/1.0 (BendingWaters research tool)"}
_TIMEOUT = 12


def _days_for_range(range_key):
    return {"7D": 7, "30D": 30, "90D": 90, "12M": 365, "5Y": 365}.get(range_key, 90)


# ---------- Feature 9: Wikipedia pageviews ----------
def _canonical_title(keyword):
    """Resolve a search term to its canonical Wikipedia article title,
    following redirects (e.g. 'artificial intelligence' -> 'Artificial intelligence').
    Pageviews are counted per exact title, so without this we'd read a redirect's
    near-zero counter. Cached with the same TTL as pageviews."""
    ckey = f"wikititle:{keyword.lower()}"

    def produce():
        try:
            r = requests.get("https://en.wikipedia.org/w/api.php",
                             headers=_UA, timeout=_TIMEOUT,
                             params={"action": "query", "titles": keyword,
                                     "redirects": 1, "format": "json"})
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for _pid, page in pages.items():
                    if "missing" not in page and page.get("title"):
                        return page["title"]
        except Exception:  # noqa: BLE001
            pass
        return keyword  # fallback: use the term as-is

    return cache.get_or_set(ckey, TTL_WIKI, produce)


def wikipedia_views(keyword, range_key):
    days = min(_days_for_range(range_key), 90)
    canonical = _canonical_title(keyword)
    title = urllib.parse.quote(canonical.replace(" ", "_"), safe="")
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    key = f"wiki:{title}:{days}"

    def produce():
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
               f"en.wikipedia/all-access/all-agents/{title}/daily/"
               f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}")
        try:
            r = requests.get(url, headers=_UA, timeout=_TIMEOUT)
            if r.status_code != 200:
                return {"total": None, "series": []}
            items = r.json().get("items", [])
            series = [{"date": it["timestamp"][:8], "views": it["views"]} for it in items]
            total = sum(it["views"] for it in items)
            return {"total": total, "series": series}
        except Exception:  # noqa: BLE001
            return {"total": None, "series": []}

    return cache.get_or_set(key, TTL_WIKI, produce)


# ---------- Feature 10: Reddit mention volume ----------
def reddit_count(keyword, range_key):
    t = {"7D": "week", "30D": "month", "90D": "year",
         "12M": "year", "5Y": "all"}.get(range_key, "month")
    key = f"reddit:{keyword}:{t}"

    def produce():
        url = "https://www.reddit.com/search.json"
        params = {"q": keyword, "limit": 100, "sort": "new", "t": t}
        try:
            r = requests.get(url, headers=_UA, params=params, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
            children = r.json().get("data", {}).get("children", [])
            return len(children)
        except Exception:  # noqa: BLE001
            return None

    return cache.get_or_set(key, TTL_SOCIAL, produce)


# ---------- Feature 21: Hacker News pulse ----------
def hn_count(keyword, range_key):
    days = min(_days_for_range(range_key), 7) if range_key == "7D" else 7
    since = int((datetime.datetime.utcnow() - datetime.timedelta(days=days)).timestamp())
    key = f"hn:{keyword}:{days}"

    def produce():
        url = "https://hn.algolia.com/api/v1/search_by_date"
        params = {"query": keyword, "tags": "story",
                  "numericFilters": f"created_at_i>{since}"}
        try:
            r = requests.get(url, headers=_UA, params=params, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
            return r.json().get("nbHits")
        except Exception:  # noqa: BLE001
            return None

    return cache.get_or_set(key, TTL_SOCIAL, produce)


# ---------- Feature 11: GNews article count ----------
def news_count(keyword):
    if not GNEWS_API_KEY:
        return None
    key = f"gnews:{keyword}"

    def produce():
        url = "https://gnews.io/api/v4/search"
        params = {"q": keyword, "token": GNEWS_API_KEY, "lang": "en", "max": 10}
        try:
            r = requests.get(url, params=params, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
            return r.json().get("totalArticles")
        except Exception:  # noqa: BLE001
            return None

    return cache.get_or_set(key, TTL_SOCIAL, produce)


def news_articles(keyword, limit=8):
    """The actual recent articles for the News drill-down (GNews)."""
    if not GNEWS_API_KEY:
        return []
    key = f"gnewsart:{keyword}:{limit}"

    def produce():
        try:
            r = requests.get("https://gnews.io/api/v4/search",
                             params={"q": keyword, "token": GNEWS_API_KEY,
                                     "lang": "en", "max": limit}, timeout=_TIMEOUT)
            if r.status_code != 200:
                return []
            return [{"title": a.get("title"), "url": a.get("url"),
                     "source": (a.get("source") or {}).get("name"),
                     "publishedAt": a.get("publishedAt"),
                     "description": a.get("description")}
                    for a in r.json().get("articles", [])]
        except Exception:  # noqa: BLE001
            return []

    return cache.get_or_set(key, TTL_SOCIAL, produce)


# ---------- Feature 12: YouTube video count ----------
def youtube_count(keyword):
    if not YOUTUBE_API_KEY:
        return None
    key = f"youtube:{keyword}"
    published_after = (datetime.datetime.utcnow()
                       - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def produce():
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": keyword, "type": "video",
                  "publishedAfter": published_after, "maxResults": 1,
                  "key": YOUTUBE_API_KEY}
        try:
            r = requests.get(url, params=params, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
            return r.json().get("pageInfo", {}).get("totalResults")
        except Exception:  # noqa: BLE001
            return None

    return cache.get_or_set(key, TTL_SOCIAL, produce)


# ---------- Feature 13: GitHub repository count ----------
def github_count(keyword):
    key = f"github:{keyword}"

    def produce():
        url = "https://api.github.com/search/repositories"
        headers = dict(_UA)
        headers["Accept"] = "application/vnd.github+json"
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        try:
            r = requests.get(url, headers=headers,
                             params={"q": keyword, "per_page": 1}, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
            return r.json().get("total_count")
        except Exception:  # noqa: BLE001
            return None

    return cache.get_or_set(key, TTL_SOCIAL, produce)


# ---------- Feature 22: Currency / market context ----------
def currency_rates():
    """USD -> NGN, ZAR. Uses open.er-api.com (free, no key) because Frankfurter
    is ECB-based and does NOT carry the Naira. Falls back to Frankfurter for ZAR."""
    key = "fx:usd"

    def produce():
        try:
            r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                rates = data.get("rates", {})
                return {
                    "base": "USD",
                    "date": data.get("time_last_update_utc", "")[:16],
                    "rates": {k: rates[k] for k in ("NGN", "ZAR") if k in rates},
                }
        except Exception:  # noqa: BLE001
            pass
        # Fallback: Frankfurter (ZAR only).
        try:
            r = requests.get("https://api.frankfurter.app/latest",
                             params={"from": "USD", "to": "ZAR"}, timeout=_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                return {"base": "USD", "date": data.get("date"),
                        "rates": data.get("rates", {})}
        except Exception:  # noqa: BLE001
            pass
        return None

    return cache.get_or_set(key, TTL_CURRENCY, produce)


# ---------- Batched enrichment for one keyword (Feature: /enrich) ----------
def enrich(keyword, range_key, include_github=False, include_hn=False):
    out = {
        "keyword": keyword,
        "wikipedia": wikipedia_views(keyword, range_key),
        "reddit": reddit_count(keyword, range_key),
        "news": news_count(keyword),
        "youtube": youtube_count(keyword),
    }
    if include_hn:
        out["hn"] = hn_count(keyword, range_key)
    if include_github:
        out["github"] = github_count(keyword)
    return out

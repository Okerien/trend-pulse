"""Free crawl provider — polite, capped, time-budgeted.

Respects robots.txt, caps page count, and stops at a wall-clock deadline so a
slow site can't stall the analysis job. Extracts just what footprint analysis
needs: title, meta description, H1/H2, and the lead paragraph.

Paid-ready: a BrightData-backed crawler can implement the same `crawl()`
signature and be swapped in via providers.py with no pipeline changes.
"""
import re
import time
import urllib.parse
import urllib.robotparser

import requests
from bs4 import BeautifulSoup

import cache

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_HEADERS = {"User-Agent": _UA, "Accept": "text/html,application/xhtml+xml"}
_TIMEOUT = 10
_TTL_CRAWL = 24 * 60 * 60  # crawled footprints change slowly; cache a day


def normalize(url):
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url):
        url = "https://" + url
    return url.rstrip("/")


def _domain(url):
    return urllib.parse.urlparse(url).netloc.lower()


def _robots(base):
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(base + "/robots.txt")
        rp.read()
    except Exception:  # noqa: BLE001 — no robots = allow
        return None
    return rp


def _sitemap_urls(base, limit=120):
    """Best-effort: pull URLs from /sitemap.xml (and one level of nested sitemaps)."""
    found = []
    try:
        r = requests.get(base + "/sitemap.xml", headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return found
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)
        for loc in locs:
            if loc.endswith(".xml") and len(found) < 4:  # nested sitemap
                try:
                    rr = requests.get(loc, headers=_HEADERS, timeout=_TIMEOUT)
                    found += re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", rr.text)
                except Exception:  # noqa: BLE001
                    pass
            else:
                found.append(loc)
            if len(found) >= limit:
                break
    except Exception:  # noqa: BLE001
        pass
    return [u for u in found if not u.endswith(".xml")][:limit]


def _extract(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = (desc_tag.get("content", "").strip() if desc_tag else "")
    headings = [h.get_text(" ", strip=True)
                for h in soup.find_all(["h1", "h2"])][:12]
    p = soup.find("p")
    lead = p.get_text(" ", strip=True)[:240] if p else ""
    return {"url": url, "title": title, "description": desc,
            "headings": headings, "lead": lead}


def crawl(url, max_pages=22, time_budget=22):
    """Return {url, domain, pages:[...], blocked, error}. Cached per (url,max_pages)."""
    base = normalize(url)
    if not base:
        return {"url": url, "pages": [], "blocked": False, "error": "invalid_url"}

    key = f"crawl:{base}:{max_pages}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    deadline = time.time() + time_budget
    rp = _robots(base)

    def allowed(u):
        if rp is None:
            return True
        try:
            return rp.can_fetch(_UA, u)
        except Exception:  # noqa: BLE001
            return True

    # Seed URL list: sitemap first, then homepage links as fallback.
    sitemap = [u for u in _sitemap_urls(base) if _domain(u) == _domain(base)]
    candidates = [base] + sitemap
    # All discovered same-domain URLs — their slugs alone reveal the topic
    # footprint cheaply, without needing to fetch every (slow) page.
    discovered = {u.rstrip("/") for u in sitemap}
    seen, pages, blocked_any = set(), [], False

    i = 0
    while i < len(candidates) and len(pages) < max_pages and time.time() < deadline:
        u = candidates[i].rstrip("/")
        i += 1
        if u in seen:
            continue
        seen.add(u)
        if not allowed(u):
            blocked_any = True
            continue
        try:
            r = requests.get(u, headers=_HEADERS, timeout=_TIMEOUT)
            if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type", ""):
                continue
            page = _extract(r.text, u)
            pages.append(page)
            # If we have no sitemap, harvest internal links from the homepage.
            if len(candidates) <= 1:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    link = urllib.parse.urljoin(base, a["href"]).split("#")[0].rstrip("/")
                    if _domain(link) == _domain(base) and link not in seen:
                        candidates.append(link)
                        discovered.add(link)
            time.sleep(0.25)  # politeness
        except Exception:  # noqa: BLE001
            continue

    result = {
        "url": base,
        "domain": _domain(base),
        "pages": pages,
        "urls": list(discovered)[:160],
        "blocked": blocked_any and not pages,  # only "blocked" if we got nothing
        "error": None if (pages or discovered) else "no_pages",
    }
    # Only cache successful crawls — never persist a flaky empty result (which
    # would otherwise serve empty for the full TTL and break a retry).
    if pages or discovered:
        cache.set(key, result, _TTL_CRAWL)
    return result

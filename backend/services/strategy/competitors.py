"""Free competitor-suggestion heuristic.

Google's related queries for a brand name routinely surface competitors
("brand vs X", "X alternative"). We mine those. It's modest by design — real
discovery is a paid Tier-2 drop-in behind the same function signature.
"""
import re
import urllib.parse

from services import pytrends_client
from config import DEMO_MODE
from services import demo
from services.strategy import websearch

_VS = re.compile(r"\b(?:vs\.?|versus|alternative to|like|compared to)\b", re.I)


def brand_name_from_url(url):
    host = urllib.parse.urlparse(url if "://" in url else "https://" + url).netloc
    host = re.sub(r"^www\.", "", host)
    return host.split(".")[0].replace("-", " ")


def suggest(website, niche, range_key="90D", geo="NG", limit=5):
    """Return [{name, url?, source}] competitor suggestions.

    Prefers Brave Search (real ranking domains + URLs); falls back to the
    pytrends related-query heuristic, then demo.
    """
    # Best: who actually ranks for the niche (real URLs we can crawl).
    # Uses Brave if a key is set, else keyless DuckDuckGo.
    if niche:
        found = websearch.discover_competitors(niche, website, limit)
        if found:
            return found

    brand = brand_name_from_url(website)
    seeds = [s for s in [brand, niche] if s]
    found, seen = [], set()

    for seed in seeds:
        data = pytrends_client.related_and_rising(seed, range_key, geo)
        for row in (data.get("related", []) + data.get("rising", [])):
            q = (row.get("query") or "").strip()
            if not q:
                continue
            # Pull the "other side" of a vs/alternative comparison.
            cand = None
            if _VS.search(q):
                parts = _VS.split(q)
                cand = parts[-1].strip() if len(parts) > 1 else None
            if cand and brand.lower() not in cand.lower():
                low = cand.lower()
                if low not in seen and 2 < len(cand) < 40:
                    seen.add(low)
                    found.append({"name": cand, "source": "related-query"})
            if len(found) >= limit:
                break
        if len(found) >= limit:
            break

    if not found and DEMO_MODE:
        return [{"name": n, "source": "sample"} for n in demo.competitors(niche or brand)]
    return found[:limit]

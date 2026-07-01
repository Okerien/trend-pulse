"""Turn crawled pages into a topic footprint: the phrases a site already covers.

Light n-gram frequency extraction (1-3 word phrases) over titles, headings, and
URL slugs. No heavy NLP dependency — good enough to compare coverage between a
brand and its competitors and to seed trend scoring.
"""
import re
import urllib.parse
from collections import Counter

_STOP = set("""
a an the and or but if then else of to in on for with at by from up down out over under
is are was were be been being do does did have has had this that these those it its as
your you we our they their he she his her them us i me my mine ours yours
how what why when where who which whom whose can will just into about more most
guide guides tips top best vs new how-to ways way using use used get make
home page blog post posts article articles read more learn 2024 2025 2026
com www http https html php amp utm html
""".split())

_WORD = re.compile(r"[a-zA-Z][a-zA-Z'+-]{1,}")


def _slug_words(url):
    path = urllib.parse.urlparse(url).path
    parts = re.split(r"[/\-_]+", path)
    return [p for p in parts if p and not p.isdigit()]


def _phrases(text, extra_stop=None):
    stop = _STOP | (extra_stop or set())
    tokens = [w.lower() for w in _WORD.findall(text or "")]
    tokens = [t for t in tokens if t not in stop and len(t) > 2]
    out = list(tokens)                                   # unigrams
    out += [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]  # bigrams
    out += [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}" for i in range(len(tokens) - 2)]
    return out


def _structural_words(urls):
    """Words appearing in most URL paths are site structure (blog, resources,
    insights, category...), not topics. Detect and drop them per-site."""
    if len(urls) < 5:
        return set()
    df = Counter()
    for u in urls:
        for w in {w.lower() for w in _slug_words(u)}:
            df[w] += 1
    n = len(urls)
    return {w for w, c in df.items() if c / n > 0.45}


def extract_topics(crawl_result, top_n=40):
    """Return {topics:[{phrase,count}], titles:[...], page_count:int, url_count:int}.

    Topics come from BOTH fetched pages (titles + headings) and the slugs of all
    discovered URLs — so coverage stays broad even when few pages were fetched.
    """
    counter = Counter()
    titles = []
    urls = crawl_result.get("urls", [])
    structural = _structural_words(urls)

    for page in crawl_result.get("pages", []):
        if page.get("title"):
            titles.append(page["title"])
        text = " ".join([
            page.get("title", ""),
            " ".join(page.get("headings", [])),
            " ".join(_slug_words(page.get("url", ""))),
        ])
        # Weight multi-word phrases a touch higher — they're more topic-specific.
        for ph in _phrases(text, structural):
            counter[ph] += 2 if " " in ph else 1

    # Slug-only topics from every discovered URL (cheap breadth, no fetch needed).
    for u in urls:
        for ph in _phrases(" ".join(_slug_words(u)), structural):
            counter[ph] += 2 if " " in ph else 1

    topics = [{"phrase": p, "count": c} for p, c in counter.most_common(top_n)]
    return {"topics": topics, "titles": titles[:60],
            "page_count": len(crawl_result.get("pages", [])),
            "url_count": len(urls)}


def topic_set(footprint):
    """Lowercased phrase set for gap comparison."""
    return {t["phrase"] for t in footprint.get("topics", [])}

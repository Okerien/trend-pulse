"""Provider swap points — this is what makes the feature "paid-ready".

The orchestrator only ever calls these names. To add a paid data source
(BrightData crawl, a SERP/SEO API, real social mining) you implement the same
signature elsewhere and reassign here — the pipeline never changes.
"""
from services.strategy import crawl as _crawl
from services.strategy import competitors as _competitors

# Free implementations (default).
crawl_site = _crawl.crawl                 # (url, max_pages, time_budget) -> footprint dict
suggest_competitors = _competitors.suggest  # (website, niche, range, geo, limit) -> [{name}]

# Paid drop-ins (future): e.g.
#   from services.strategy.brightdata import crawl_site as crawl_site
#   from services.strategy.serpapi import discover_competitors as suggest_competitors

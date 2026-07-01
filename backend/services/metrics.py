"""Calculated features — no external API. Pure analysis of the trend series.

Covers:
  - Feature 14: momentum score (0-100)
  - Feature 15: breakout flag
  - Feature 16: seasonality detection
  - Feature 18: best time to publish
"""
import numpy as np


def momentum(values, regions_above_50=None):
    """Feature 14 — momentum score 0-100.

    Three components:
      - slope of the last 4 points          (weight 50%)
      - current value / peak value          (weight 30%)
      - share of regions above 50 interest  (weight 20%)

    `regions_above_50` is (count, total). When None (the common case, since
    fetching regional data for every card is rate-limit-expensive), the
    regional component is dropped and the other two weights are renormalised
    so the score still spans 0-100. See teach-point #1.
    """
    values = [v for v in values if v is not None]
    if len(values) < 2:
        return 0

    # Component 1: slope of last 4 points, mapped to 0-1.
    tail = values[-4:]
    xs = np.arange(len(tail))
    slope = np.polyfit(xs, tail, 1)[0]  # interest points per step
    # A slope of +5/step is very strong; clamp to [-5, 5] then map to [0,1].
    slope_score = np.clip((slope + 5) / 10, 0, 1)

    # Component 2: current / peak.
    peak = max(values) or 1
    peak_ratio = values[-1] / peak  # already 0-1

    if regions_above_50 is not None:
        count, total = regions_above_50
        breadth = (count / total) if total else 0
        score = 100 * (0.50 * slope_score + 0.30 * peak_ratio + 0.20 * breadth)
    else:
        # Renormalise 50/30 -> 62.5/37.5 so we still use the full 0-100 range.
        score = 100 * (0.625 * slope_score + 0.375 * peak_ratio)

    return round(float(score))


def momentum_band(score):
    """Green / amber / red band for the card colour indicator."""
    if score >= 70:
        return "green"
    if score >= 40:
        return "amber"
    return "red"


def is_breakout(values):
    """Feature 15 — True if recent-quarter avg is >50% above first-quarter avg."""
    values = [v for v in values if v is not None]
    n = len(values)
    if n < 4:
        return False
    q = max(1, n // 4)
    first = np.mean(values[:q])
    last = np.mean(values[-q:])
    if first <= 0:
        return bool(last > 0)
    return bool((last - first) / first > 0.50)


def best_publish_time(dates, values):
    """Feature 18 — day-of-week + week-of-month with highest avg interest.

    `dates` is a list of datetime objects aligned with `values`.
    Returns a dict or None if there isn't enough daily granularity.
    """
    if not dates or len(dates) != len(values):
        return None

    dow_totals, dow_counts = {}, {}
    wom_totals, wom_counts = {}, {}
    for d, v in zip(dates, values):
        if v is None:
            continue
        dow = d.weekday()  # 0=Mon
        wom = (d.day - 1) // 7 + 1  # 1..5
        dow_totals[dow] = dow_totals.get(dow, 0) + v
        dow_counts[dow] = dow_counts.get(dow, 0) + 1
        wom_totals[wom] = wom_totals.get(wom, 0) + v
        wom_counts[wom] = wom_counts.get(wom, 0) + 1

    if not dow_counts or not wom_counts:
        return None

    best_dow = max(dow_totals, key=lambda k: dow_totals[k] / dow_counts[k])
    best_wom = max(wom_totals, key=lambda k: wom_totals[k] / wom_counts[k])

    dow_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    ordinals = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "last"}
    return {
        "day_of_week": dow_names[best_dow],
        "week_of_month": ordinals.get(best_wom, "third"),
        "sentence": (
            f"Search interest peaks on {dow_names[best_dow]}s "
            f"in the {ordinals.get(best_wom, 'third')} week of the month."
        ),
    }


def detect_seasonality(dates, values):
    """Feature 16 — compare the recent window against the same calendar window
    in prior years using a ~5-year daily/weekly series.

    Returns "seasonal", "seasonal_plus", or None (not enough history / not seasonal).
    """
    if not dates or len(dates) < 200:
        return None  # need multi-year history

    import datetime
    latest = dates[-1]
    # Define the "current window" as the last 30 days.
    window_start = latest - datetime.timedelta(days=30)
    current_vals = [v for d, v in zip(dates, values)
                    if window_start <= d <= latest and v is not None]
    if not current_vals:
        return None
    current_avg = float(np.mean(current_vals))

    # Same calendar window (day-of-year +-15) in each of the previous 4 years.
    matches = 0
    prior_avgs = []
    for years_back in range(1, 5):
        try:
            ref = latest.replace(year=latest.year - years_back)
        except ValueError:
            ref = latest - datetime.timedelta(days=365 * years_back)
        lo = ref - datetime.timedelta(days=15)
        hi = ref + datetime.timedelta(days=15)
        window_vals = [v for d, v in zip(dates, values)
                       if lo <= d <= hi and v is not None]
        if not window_vals:
            continue
        avg = float(np.mean(window_vals))
        prior_avgs.append(avg)
        # "Spike" in that year if its window avg is meaningfully above its own yearly baseline.
        year_vals = [v for d, v in zip(dates, values)
                     if d.year == ref.year and v is not None]
        baseline = float(np.mean(year_vals)) if year_vals else 0
        if baseline and avg > baseline * 1.15:
            matches += 1

    if matches < 3:
        return None
    # Seasonal. Is this year's spike bigger than the historical average for the window?
    if prior_avgs and current_avg > float(np.mean(prior_avgs)) * 1.15:
        return "seasonal_plus"
    return "seasonal"

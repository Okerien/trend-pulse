"""Feature 17 — Pearson correlation matrix across active keywords.

Generated entirely from data already fetched. No external API calls.
"""
import numpy as np


def correlation_matrix(series_by_keyword):
    """`series_by_keyword`: {keyword: [values...]} aligned by index.

    Returns a list of pairwise results:
      [{"a": kw1, "b": kw2, "r": 0.83, "note": "..."}]
    """
    keywords = list(series_by_keyword.keys())
    results = []
    for i in range(len(keywords)):
        for j in range(i + 1, len(keywords)):
            a, b = keywords[i], keywords[j]
            va = np.array(series_by_keyword[a], dtype=float)
            vb = np.array(series_by_keyword[b], dtype=float)
            n = min(len(va), len(vb))
            if n < 3:
                continue
            va, vb = va[:n], vb[:n]
            if va.std() == 0 or vb.std() == 0:
                r = 0.0
            else:
                r = float(np.corrcoef(va, vb)[0, 1])
            results.append({"a": a, "b": b, "r": round(r, 2), "note": _note(r)})
    return results


def _note(r):
    if r > 0.8:
        return "Strongly correlated — likely the same audience intent."
    if r < -0.5:
        return "Inversely correlated — may be substitutes in the market."
    return ""

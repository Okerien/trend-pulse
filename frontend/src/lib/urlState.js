// Features 8 & 19 — one encoder/decoder powering BOTH the shareable link and
// the client report URL. State lives in the query string so any link is live.
//
//   ?keywords=a,b&range=90D&geo=NG            -> normal shared view
//   /report?client=OaksPlace&keywords=...     -> branded client report

export function readState() {
  const p = new URLSearchParams(window.location.search);
  const keywords = (p.get("keywords") || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return {
    keywords,
    range: (p.get("range") || "90D").toUpperCase(),
    geo: (p.get("geo") || "NG").toUpperCase(),
    report: window.location.pathname.replace(/\/$/, "").endsWith("/report"),
    client: p.get("client") || "",
  };
}

export function buildQuery({ keywords, range, geo, client }) {
  const p = new URLSearchParams();
  if (keywords?.length) p.set("keywords", keywords.join(","));
  if (range) p.set("range", range);
  if (geo) p.set("geo", geo);
  if (client) p.set("client", client);
  return p.toString();
}

// Push state into the address bar without reloading (Feature 4/5 preserve on share).
export function syncUrl({ keywords, range, geo }) {
  const isReport = window.location.pathname.replace(/\/$/, "").endsWith("/report");
  if (isReport) return; // never rewrite a report URL out from under the client
  const qs = buildQuery({ keywords, range, geo });
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", url);
}

export function shareUrl(state) {
  const qs = buildQuery(state);
  return `${window.location.origin}${window.location.pathname}?${qs}`;
}

export function reportUrl({ keywords, range, geo, client }) {
  const origin = window.location.origin;
  const qs = buildQuery({ keywords, range, geo, client });
  return `${origin}/report?${qs}`;
}

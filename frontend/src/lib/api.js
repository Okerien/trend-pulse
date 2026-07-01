// Thin fetch wrappers around the 8 backend endpoints.
const BASE = (import.meta.env.VITE_API_URL || "http://localhost:5000").replace(/\/$/, "");

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${path} -> HTTP ${res.status}`);
  return res.json();
}

const kwParam = (keywords) => keywords.join(",");

export const api = {
  trends: (keywords, range, geo) =>
    get("/trends", { keywords: kwParam(keywords), range, geo }),

  news: (keyword) => get("/news", { keyword }),
  history: (keyword, geo) => get("/history", { keyword, geo }),

  trending: (niche, range, geo) => get("/trending", { niche, range, geo }),

  detail: (keyword, range, geo) => get("/detail", { keyword, range, geo }),

  enrich: (keyword, range, niche, opts = {}) =>
    get("/enrich", {
      keyword,
      range,
      niche,
      github: opts.github ? 1 : undefined,
      hn: opts.hn ? 1 : undefined,
    }),

  correlate: (keywords, range, geo) =>
    get("/correlate", { keywords: kwParam(keywords), range, geo }),

  context: () => get("/context"),

  summarise: async (payload) => {
    const res = await fetch(BASE + "/summarise", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok && res.status !== 400) throw new Error(`/summarise -> ${res.status}`);
    return res.json();
  },

  strategy: {
    analyze: (body) => post("/strategy/analyze", body),
    status: (jobId) => get("/strategy/status", { job_id: jobId }),
    result: async (jobId) => {
      const res = await fetch(`${BASE}/strategy/result?job_id=${encodeURIComponent(jobId)}`);
      return res.json();
    },
    suggestCompetitors: (website, niche, geo) =>
      get("/strategy/suggest-competitors", { website, niche, geo }),
    draft: (item, voice) => post("/strategy/draft", { item, voice }),
  },

  ai: {
    read: (kw) => post("/ai/read", kw),
    reads: (keywords) => post("/ai/reads", { keywords }),
    correlateNote: (pairs) => post("/ai/correlate-note", { pairs }),
    suggest: (seed, n = 6) => get("/ai/suggest", { seed, n }),
    niche: (niche) => get("/ai/niche", { niche }),
    ask: (question, context) => post("/ai/ask", { question, context }),
    why: (keyword, geo) => get("/ai/why", { keyword, geo }),
  },
};

async function post(path, body) {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok && res.status !== 400) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export { BASE };

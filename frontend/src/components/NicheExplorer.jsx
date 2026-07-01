import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { Refresh, Plus, Sparkle } from "./Icons";

// Feature 7 — eight pre-loaded niches; top-10 trending; one-click add.
const NICHES = [
  ["digital_marketing", "Digital Marketing"],
  ["ecommerce", "E-commerce"],
  ["real_estate", "Real Estate"],
  ["health_wellness", "Health & Wellness"],
  ["finance_fintech", "Finance & Fintech"],
  ["ai_technology", "AI & Technology"],
  ["fashion_beauty", "Fashion & Beauty"],
  ["food_restaurants", "Food & Restaurants"],
];

export default function NicheExplorer() {
  const { geo, range, addKeyword } = useApp();
  const [niche, setNiche] = useState(NICHES[0][0]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ai, setAi] = useState(null);

  const label = NICHES.find(([k]) => k === niche)?.[1] || niche;

  function load(n = niche) {
    setLoading(true);
    api.trending(n, range, geo)
      .then((r) => setItems(r.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(niche); /* eslint-disable-next-line */ }, [niche, geo, range]);

  useEffect(() => {
    setAi(null);
    api.ai.niche(label).then((r) => setAi(r.ok ? r : null)).catch(() => setAi(null));
  }, [label]);

  return (
    <div>
      <div className="niche-tabs">
        {NICHES.map(([key, lbl]) => (
          <button key={key} className={key === niche ? "active" : ""} onClick={() => setNiche(key)}>
            {lbl}
          </button>
        ))}
      </div>

      <div className="panel ai-niche">
        <div className="ai-niche-head"><Sparkle size={14} /> AI niche read</div>
        {ai == null ? (
          <p className="why-load">Analyzing the {label} niche…</p>
        ) : (
          <>
            <p className="ai-niche-state">{ai.state}</p>
            {ai.keywords?.length > 0 && (
              <div className="ai-niche-kws">
                {ai.keywords.map((k, i) => (
                  <button key={i} className="add-chip" onClick={() => addKeyword(k)}><Plus size={12} /> {k}</button>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <div className="panel">
        <div className="panel-head">
          <h3>Top trending {loading && <span className="spinner" />}</h3>
          <div className="spacer" />
          <button className="ghost-btn" onClick={() => load()}><Refresh size={14} /> Refresh</button>
        </div>

        {items.length === 0 && !loading ? (
          <p className="corr-note" style={{ padding: "10px 2px" }}>
            No trending data returned for this niche/region right now — try Refresh or another region.
          </p>
        ) : (
          <div className="trend-list">
            {items.map((it, i) => (
              <div className="trend-item" key={i}>
                <span className="rank">{i + 1}</span>
                <span className="q">{it.query}</span>
                {it.value != null && <span className="v">{formatVal(it.value)}</span>}
                <button className="add-btn" title="Add to tracker" onClick={() => addKeyword(it.query)}><Plus size={15} /></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function formatVal(v) {
  if (v >= 1000) return "+" + (v >= 1e6 ? (v / 1e6).toFixed(1) + "M" : (v / 1e3).toFixed(0) + "k") + "%";
  return v >= 100 ? v : v + "";
}

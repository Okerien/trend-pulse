import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { Sparkle } from "./Icons";

// Feature 17 — pairwise Pearson correlation, shown when 2+ keywords are active.
export default function CorrelationMatrix() {
  const { keywords, range, geo } = useApp();
  const [pairs, setPairs] = useState([]);
  const [note, setNote] = useState("");

  useEffect(() => {
    if (keywords.length < 2) { setPairs([]); setNote(""); return; }
    let alive = true;
    api.correlate(keywords, range, geo)
      .then((r) => {
        if (!alive) return;
        const ps = r.pairs || [];
        setPairs(ps);
        if (ps.length) api.ai.correlateNote(ps).then((n) => alive && setNote(n.note || "")).catch(() => {});
      })
      .catch(() => {});
    return () => { alive = false; };
  }, [keywords, range, geo]);

  if (keywords.length < 2 || !pairs.length) return null;

  return (
    <div className="panel">
      <div className="panel-head"><h3>Correlations</h3></div>
      {note && <p className="corr-ai"><Sparkle size={13} /> {note}</p>}
      <div className="corr-list">
        {pairs.map((p, i) => {
          const cls = p.r > 0.8 ? "high" : p.r < -0.5 ? "inv" : "mid";
          return (
            <div className="corr-row" key={i}>
              <span className={"corr-r " + cls}>{p.r > 0 ? "+" : ""}{p.r.toFixed(2)}</span>
              <span className="corr-pair">{p.a} ↔ {p.b}</span>
              {p.note && <span className="corr-note">— {p.note}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

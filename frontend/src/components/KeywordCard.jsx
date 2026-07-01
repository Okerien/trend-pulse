import { useEffect, useState } from "react";
import Sparkline from "./Sparkline";
import MomentumGauge from "./MomentumGauge";
import NewsModal from "./NewsModal";
import { api } from "../lib/api";
import { Bookmark, Close, Bolt, Calendar, Sparkle } from "./Icons";

// Feature 1,2,9-16,20,21 + inline AI read (batched) + news drill-down.
export default function KeywordCard({ kw, dates, color, range, read, pinned, onTogglePin, onOpen, onRemove }) {
  const [enrich, setEnrich] = useState(null);
  const [showWiki, setShowWiki] = useState(false);
  const [newsOpen, setNewsOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    setEnrich(null);
    api.enrich(kw.keyword, range, "", { hn: false, github: false })
      .then((e) => alive && setEnrich(e))
      .catch(() => {});
    return () => { alive = false; };
  }, [kw.keyword, range]);

  const band = kw.band || "amber";
  const delta = kw.change_pct;
  const hasNews = enrich?.news != null && enrich.news > 0;

  return (
    <div className="card" style={{ "--accent": color }}>
      <div className="kw-head">
        <div className="kw-name" onClick={onOpen} title="Open details">{kw.keyword}</div>
        <button className={"iconbtn" + (pinned ? " on" : "")} title="Watchlist"
          onClick={() => onTogglePin(kw.keyword)}><Bookmark filled={pinned} size={15} /></button>
        <button className="iconbtn" title="Remove" onClick={() => onRemove(kw.keyword)}><Close size={15} /></button>
      </div>

      <div className="score-row">
        <MomentumGauge value={kw.momentum ?? 0} band={band} />
        <div className="score-meta">
          <div className="score-label">Momentum</div>
          {kw.latest != null && <div className="latest-line">Interest <b className="num">{kw.latest}</b></div>}
          {delta != null && (
            <div className={delta >= 0 ? "delta up" : "delta down"}>
              {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}%
            </div>
          )}
        </div>
      </div>

      <div className="ai-read">
        <Sparkle size={13} />
        {read === undefined ? <span className="ai-read-load">Reading the signals…</span>
          : read ? <span>{read}</span>
          : <span className="ai-read-load">No AI read available.</span>}
      </div>

      <div className="badges">
        {kw.breakout && <span className="badge breakout"><Bolt size={11} /> Breakout</span>}
        {kw.seasonality === "seasonal" && <span className="badge seasonal"><Calendar size={11} /> Seasonal</span>}
        {kw.seasonality === "seasonal_plus" && <span className="badge seasonal-plus"><Calendar size={11} /> Seasonal+</span>}
        {enrich?.news != null && (
          <button className={"badge" + (hasNews ? " clickable" : "")} disabled={!hasNews}
            onClick={() => hasNews && setNewsOpen(true)} title={hasNews ? "Read articles" : ""}>
            <span className="k">News</span> <span className="v">{fmt(enrich.news)}</span>
          </button>
        )}
        {enrich?.reddit != null && <span className="badge"><span className="k">Reddit</span> <span className="v">{fmt(enrich.reddit)}</span></span>}
        {enrich?.youtube != null && <span className="badge"><span className="k">YouTube</span> <span className="v">{fmt(enrich.youtube)}</span></span>}
      </div>

      <Sparkline dates={dates} values={kw.values} color={color}
        wiki={enrich?.wikipedia} showWiki={showWiki} />

      {enrich?.wikipedia?.total != null && (
        <div className="toggle-row" onClick={() => setShowWiki((s) => !s)} role="button">
          <span className={"switch" + (showWiki ? " on" : "")} />
          Wikipedia overlay
          <span className="meta">{fmt(enrich.wikipedia.total)} views</span>
        </div>
      )}

      {newsOpen && <NewsModal keyword={kw.keyword} onClose={() => setNewsOpen(false)} />}
    </div>
  );
}

function fmt(n) {
  if (n == null) return "—";
  if (n >= 1e6) return (n / 1e6).toFixed(1) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "k";
  return String(n);
}

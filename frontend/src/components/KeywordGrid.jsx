import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { colorFor } from "../lib/colors";
import { togglePin, isPinned } from "../lib/watchlist";
import { api } from "../lib/api";
import KeywordCard from "./KeywordCard";

export default function KeywordGrid({ onOpen }) {
  const { data, keywords, range, watchlist, setWatchlist, removeKeyword, loading } = useApp();
  const [reads, setReads] = useState({});

  // One batched AI-reads call for all cards (rate-limit safe), not N calls.
  useEffect(() => {
    if (!data.keywords.length) return;
    let alive = true;
    const payload = data.keywords.map((k) => ({
      keyword: k.keyword, momentum: k.momentum, band: k.band,
      breakout: k.breakout, seasonality: k.seasonality, change_pct: k.change_pct,
    }));
    api.ai.reads(payload).then((r) => alive && setReads(r.reads || {})).catch(() => {});
    return () => { alive = false; };
  }, [data.keywords]);

  if (!keywords.length) return null;

  if (loading && data.keywords.length === 0) {
    return (
      <div className="grid">
        {keywords.map((kw) => (
          <div className="skeleton-card" key={kw}>
            <div className="sk" style={{ height: 16, width: "55%" }} />
            <div className="sk" style={{ height: 36, width: "40%", marginTop: 16 }} />
            <div className="sk" style={{ height: 20, width: "70%", marginTop: 14 }} />
            <div className="sk" style={{ height: 56, width: "100%", marginTop: 16 }} />
          </div>
        ))}
      </div>
    );
  }

  const onTogglePin = (kw) => setWatchlist((m) => togglePin(m, kw));

  return (
    <div className="grid">
      {data.keywords.map((kw) => (
        <KeywordCard
          key={kw.keyword}
          kw={kw}
          dates={data.dates}
          range={range}
          color={colorFor(kw.keyword, keywords)}
          read={reads[kw.keyword]}
          pinned={isPinned(watchlist, kw.keyword)}
          onTogglePin={onTogglePin}
          onOpen={() => onOpen(kw.keyword)}
          onRemove={removeKeyword}
        />
      ))}
    </div>
  );
}

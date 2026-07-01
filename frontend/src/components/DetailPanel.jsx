import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { colorFor } from "../lib/colors";
import { useChartTheme } from "../lib/useChartTheme";
import { Close, Calendar, External, Bolt, Sparkle, Link } from "./Icons";

// Feature 6 — slide-in detail + grounded "why now" research.
export default function DetailPanel({ keyword, onClose, onAsk }) {
  const { range, geo, keywords } = useApp();
  const t = useChartTheme();
  const [d, setD] = useState(null);
  const [why, setWhy] = useState(null);

  useEffect(() => {
    setD(null);
    api.detail(keyword, range, geo).then(setD).catch(() => setD({ error: true }));
  }, [keyword, range, geo]);

  useEffect(() => {
    setWhy(null);
    api.ai.why(keyword, geo).then((r) => setWhy(r.ok ? r : { answer: "" })).catch(() => setWhy({ answer: "" }));
  }, [keyword, geo]);

  const [hist, setHist] = useState([]);
  useEffect(() => {
    api.history(keyword, geo).then((r) => setHist(r.history || [])).catch(() => setHist([]));
  }, [keyword, geo]);

  const color = colorFor(keyword, keywords.length ? keywords : [keyword]);
  const rows = (d?.dates || []).map((date, i) => ({ date, value: d.values?.[i] ?? null }));

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="drawer">
        <button className="iconbtn close" onClick={onClose}><Close size={18} /></button>
        <div className="drawer-inner">
          <h2>{keyword}</h2>
          <div className="corr-note">{geo} · {range}</div>

          {!d ? (
            <p style={{ marginTop: 30 }}><span className="spinner" /> Loading…</p>
          ) : d.error ? (
            <p style={{ marginTop: 20 }} className="corr-note">Couldn’t load details right now.</p>
          ) : (
            <>
              <div className="kv">
                <div className="box"><div className="l">Momentum</div><div className={"v " + (d.band || "")}>{d.momentum}</div></div>
                <div className="box"><div className="l">Status</div><div className="v" style={{ fontSize: 15, fontFamily: "var(--font)", display: "flex", alignItems: "center", gap: 6 }}>
                  {d.breakout ? <><Bolt size={15} /> Breakout</> : d.seasonality === "seasonal_plus" ? <><Calendar size={15} /> Seasonal+</>
                    : d.seasonality === "seasonal" ? <><Calendar size={15} /> Seasonal</> : "Stable"}</div></div>
              </div>

              {d.best_time?.sentence && (
                <p className="best-time"><Calendar size={16} /> {d.best_time.sentence}</p>
              )}

              <div className="why-now">
                <div className="why-head"><Sparkle size={14} /> Why it's trending now</div>
                {why == null ? (
                  <p className="why-load">Researching live sources…</p>
                ) : why.answer ? (
                  <>
                    <p className="why-text">{why.answer}</p>
                    {why.citations?.length > 0 && (
                      <div className="why-cites">
                        {why.citations.map((c) => (
                          <a key={c.n} href={c.url} target="_blank" rel="noreferrer" title={c.title}>
                            <Link size={11} /> {c.n}. {host(c.url)}
                          </a>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <p className="why-load">No live context found right now.</p>
                )}
                {onAsk && <button className="ghost-btn why-ask" onClick={() => onAsk(`Tell me more about why "${keyword}" is trending and what marketers should do.`)}><Sparkle size={13} /> Ask the copilot</button>}
              </div>

              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
                  <CartesianGrid stroke={t.grid} vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: t.tick }} minTickGap={40} axisLine={{ stroke: t.grid }} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: t.tick }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 9, fontSize: 12, background: t.surface, border: `1px solid ${t.border}`, color: t.text }} itemStyle={{ color: t.text }} labelStyle={{ color: t.faint }} />
                  <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2.4} dot={false} />
                </LineChart>
              </ResponsiveContainer>

              {hist.length >= 2 && (
                <>
                  <div className="section-title">Momentum tracked over time</div>
                  <ResponsiveContainer width="100%" height={120}>
                    <LineChart data={hist} margin={{ top: 6, right: 8, bottom: 0, left: -22 }}>
                      <CartesianGrid stroke={t.grid} vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 9, fill: t.tick }} minTickGap={50} axisLine={{ stroke: t.grid }} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: t.tick }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ borderRadius: 9, fontSize: 12, background: t.surface, border: `1px solid ${t.border}`, color: t.text }} />
                      <Line type="monotone" dataKey="momentum" stroke={color} strokeWidth={2.2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </>
              )}

              <Section title="Rising searches" items={d.rising} rise />
              <Section title="Related queries" items={d.related} />

              {d.regional?.length > 0 && (
                <>
                  <div className="section-title">Regional interest</div>
                  <ul className="qlist">
                    {d.regional.slice(0, 8).map((r, i) => (
                      <li key={i}><span>{r.name}</span><span>{r.value}</span></li>
                    ))}
                  </ul>
                </>
              )}

              {d.google_trends_url && (
                <a className="ghost-btn accent" style={{ display: "inline-flex", marginTop: 18, textDecoration: "none" }}
                  href={d.google_trends_url} target="_blank" rel="noreferrer">Open in Google Trends <External size={14} /></a>
              )}
            </>
          )}
        </div>
      </aside>
    </>
  );
}

function Section({ title, items, rise }) {
  if (!items?.length) return null;
  return (
    <>
      <div className="section-title">{title}</div>
      <ul className="qlist">
        {items.slice(0, 8).map((q, i) => (
          <li key={i}>
            <span>{q.query}</span>
            <span className={rise ? "rise" : ""}>{rise ? formatRise(q.value) : q.value}</span>
          </li>
        ))}
      </ul>
    </>
  );
}

function formatRise(v) {
  if (v == null) return "";
  if (v >= 1000) return "Breakout";
  return "+" + v + "%";
}

const host = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return "source"; } };

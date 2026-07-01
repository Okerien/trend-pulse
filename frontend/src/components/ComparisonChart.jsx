import { useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { useApp } from "../context/AppContext";
import { colorFor } from "../lib/colors";
import { exportPng } from "../lib/exportPng";
import { exportCsv } from "../lib/exportCsv";
import { shareUrl } from "../lib/urlState";
import { useChartTheme } from "../lib/useChartTheme";
import { Sparkle } from "./Icons";

// Feature 3 (comparison chart), 8 (export suite), 23 (Generate insight trigger).
export default function ComparisonChart({ onGenerate, generating, onToast, bare = false }) {
  const { data, keywords, range, geo } = useApp();
  const t = useChartTheme();
  const chartRef = useRef(null);

  if (!keywords.length || !data.dates.length) return null;

  const rows = data.dates.map((date, i) => {
    const row = { date };
    data.keywords.forEach((kw) => { row[kw.keyword] = kw.values?.[i] ?? null; });
    return row;
  });

  async function doShare() {
    const url = shareUrl({ keywords, range, geo });
    try { await navigator.clipboard.writeText(url); onToast("Share link copied to clipboard"); }
    catch { onToast(url); }
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>{bare ? "Live trend comparison" : "Comparison"}</h3>
        {!bare && (
          <>
            <div className="spacer" />
            <button className="ghost-btn" onClick={() => exportPng(chartRef.current, `trend-pulse_${geo}_${range}.png`)}>PNG</button>
            <button className="ghost-btn" onClick={() => exportCsv({ dates: data.dates, keywords: data.keywords, range, geo })}>CSV</button>
            <button className="ghost-btn" onClick={doShare}>Share link</button>
            <button className="ghost-btn accent" onClick={onGenerate} disabled={generating}>
              {generating ? <><span className="spinner" /> Generating…</> : <><Sparkle size={14} /> Generate insight</>}
            </button>
          </>
        )}
      </div>

      <div ref={chartRef} style={{ background: t.surface, padding: "8px 4px 0", borderRadius: 10 }}>
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={rows} margin={{ top: 10, right: 16, bottom: 0, left: -16 }}>
            <CartesianGrid stroke={t.grid} vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: t.tick }} minTickGap={42}
              axisLine={{ stroke: t.grid }} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: t.tick }}
              axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: 10, border: `1px solid ${t.border}`,
              background: t.surface, color: t.text, fontSize: 12, boxShadow: "var(--shadow)" }}
              itemStyle={{ color: t.text }} labelStyle={{ color: t.faint }} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
            {data.keywords.map((kw) => (
              <Line key={kw.keyword} type="monotone" dataKey={kw.keyword}
                stroke={colorFor(kw.keyword, keywords)} strokeWidth={2.2} dot={false}
                connectNulls animationDuration={650} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

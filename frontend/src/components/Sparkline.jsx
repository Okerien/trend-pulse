import { LineChart, Line, Tooltip, ResponsiveContainer, YAxis } from "recharts";
import { muted } from "../lib/colors";
import { useChartTheme } from "../lib/useChartTheme";

// Feature 2 — animated inline sparkline with hover tooltip; matches keyword colour.
// Feature 9 — optional muted Wikipedia overlay line.
export default function Sparkline({ dates, values, color, wiki, showWiki, height = 56 }) {
  const t = useChartTheme();
  const data = (values || []).map((v, i) => ({
    date: dates[i],
    value: v,
    wiki: showWiki && wiki ? wikiAt(wiki, dates[i]) : undefined,
  }));

  return (
    <div className="spark">
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
          <YAxis hide domain={[0, 100]} />
          {showWiki && wiki && (
            <Line type="monotone" dataKey="wiki" stroke={muted(color)} strokeWidth={1.5}
              dot={false} isAnimationActive />
          )}
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2.4}
            dot={false} animationDuration={700} />
          <Tooltip
            contentStyle={{ borderRadius: 10, border: `1px solid ${t.border}`,
              background: t.surface, color: t.text, fontSize: 12, boxShadow: "var(--shadow)" }}
            labelStyle={{ color: t.faint, fontSize: 11 }}
            itemStyle={{ color: t.text }}
            formatter={(val, name) => [val, name === "wiki" ? "Wikipedia" : "Interest"]}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function wikiAt(wiki, isoDate) {
  if (!wiki?.series?.length) return undefined;
  const key = (isoDate || "").replaceAll("-", "");
  const max = Math.max(...wiki.series.map((s) => s.views), 1);
  const hit = wiki.series.find((s) => s.date === key);
  return hit ? Math.round((hit.views / max) * 100) : undefined;
}

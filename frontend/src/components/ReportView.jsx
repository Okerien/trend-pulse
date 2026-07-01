import { useApp } from "../context/AppContext";
import { colorFor } from "../lib/colors";
import ComparisonChart from "./ComparisonChart";
import CorrelationMatrix from "./CorrelationMatrix";
import { Bolt, Calendar } from "./Icons";

// Feature 19 — client report mode: chrome hidden, client name shown, chart-forward.
export default function ReportView() {
  const { client, data, keywords, geo, range } = useApp();

  return (
    <div className="report">
      <div className="container report-head">
        {client && <div className="client-name">Prepared for {client}</div>}
        <h1>Search Trend Report</h1>
        <div className="powered">{geo} · {range} · live data · powered by BendingWaters</div>
      </div>

      <div className="container" style={{ paddingBottom: 50 }}>
        <div className="grid" style={{ margin: "18px 0 22px", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
          {data.keywords.map((kw) => (
            <div className="card" key={kw.keyword} style={{ "--accent": colorFor(kw.keyword, keywords) }}>
              <div className="kw-name" style={{ cursor: "default" }}>{kw.keyword}</div>
              <div className="score-row">
                <span className={"score " + (kw.band || "")}>{kw.momentum}</span>
                <div className="score-meta"><div className="score-label">Momentum</div></div>
              </div>
              <div className="badges">
                {kw.latest != null && <span className="badge"><span className="k">Interest</span> <span className="v">{kw.latest}</span></span>}
                {kw.breakout && <span className="badge breakout"><Bolt size={11} /> Breakout</span>}
                {kw.seasonality === "seasonal" && <span className="badge seasonal"><Calendar size={11} /> Seasonal</span>}
                {kw.seasonality === "seasonal_plus" && <span className="badge seasonal-plus"><Calendar size={11} /> Seasonal+</span>}
              </div>
            </div>
          ))}
        </div>

        <ComparisonChart bare />
        <div style={{ height: 18 }} />
        <CorrelationMatrix />
      </div>
    </div>
  );
}

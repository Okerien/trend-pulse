import { useApp } from "../context/AppContext";
import { Sun, Moon, Search, Command } from "./Icons";

const RANGES = ["7D", "30D", "90D", "12M", "5Y"];
const REGIONS = [
  { code: "NG", label: "Nigeria" },
  { code: "ZA", label: "South Africa" },
  { code: "US", label: "United States" },
  { code: "GB", label: "United Kingdom" },
  { code: "GLOBAL", label: "Global" },
];

// Feature 4 (range), Feature 5 (region), Feature 19 (report toggle), theme toggle.
export default function TopBar({ onToggleReport }) {
  const { range, setRange, geo, setGeo, theme, toggleTheme } = useApp();
  return (
    <header className="topbar">
      <div className="container">
        <div className="logo">
          <span className="mark"><span /></span>
          Trend&nbsp;Pulse <small>by BendingWaters</small>
        </div>
        <div className="spacer" />

        <button className="cmdk-trigger" onClick={() => window.dispatchEvent(new Event("trendpulse:cmdk"))}>
          <Search size={14} /> <span>Search or ask…</span>
          <span className="kbd"><Command size={10} />K</span>
        </button>

        <div className="pillstrip" role="tablist" aria-label="Time range">
          {RANGES.map((r) => (
            <button key={r} className={r === range ? "active" : ""} onClick={() => setRange(r)}>
              {r}
            </button>
          ))}
        </div>

        <select className="region" value={geo} onChange={(e) => setGeo(e.target.value)} aria-label="Region">
          {REGIONS.map((r) => (
            <option key={r.code} value={r.code}>{r.label}</option>
          ))}
        </select>

        <button className="ghost-btn" onClick={onToggleReport}>Client view</button>
        <button className="icon-toggle" onClick={toggleTheme}
          aria-label="Toggle theme" title="Toggle light / dark">
          {theme === "dark" ? <Sun /> : <Moon />}
        </button>
      </div>
    </header>
  );
}

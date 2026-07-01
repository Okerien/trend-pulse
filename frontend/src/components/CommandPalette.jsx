import { useEffect, useMemo, useRef, useState } from "react";
import { Search, Sparkle, Plus, Compass, Calendar, Globe, Sun, Bookmark, Command } from "./Icons";

// ⌘K command palette — add keywords, navigate, change range/region, ask AI.
export default function CommandPalette({ actions }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    const openEvt = () => setOpen(true);
    window.addEventListener("keydown", onKey);
    window.addEventListener("trendpulse:cmdk", openEvt);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("trendpulse:cmdk", openEvt);
    };
  }, []);

  useEffect(() => {
    if (open) { setQ(""); setActive(0); setTimeout(() => inputRef.current?.focus(), 30); }
  }, [open]);

  const base = useMemo(() => [
    { icon: Compass, label: "Go to Keyword Tracker", run: () => actions.setTab("tracker"), group: "Navigate" },
    { icon: Compass, label: "Go to Niche Explorer", run: () => actions.setTab("niche"), group: "Navigate" },
    { icon: Compass, label: "Go to Content Studio", run: () => actions.setTab("studio"), group: "Navigate" },
    { icon: Bookmark, label: "Open Watchlist", run: () => actions.openWatchlist(), group: "Navigate" },
    { icon: Sparkle, label: "Generate AI insight", run: () => actions.generateInsight(), group: "AI" },
    ...["7D", "30D", "90D", "12M", "5Y"].map((r) => ({
      icon: Calendar, label: `Set range ${r}`, run: () => actions.setRange(r), group: "Range" })),
    ...[["NG", "Nigeria"], ["ZA", "South Africa"], ["US", "United States"], ["GB", "United Kingdom"], ["GLOBAL", "Global"]]
      .map(([code, name]) => ({ icon: Globe, label: `Region: ${name}`, run: () => actions.setGeo(code), group: "Region" })),
    { icon: Sun, label: "Toggle light / dark theme", run: () => actions.toggleTheme(), group: "App" },
  ], [actions]);

  const items = useMemo(() => {
    const dyn = [];
    if (q.trim()) {
      dyn.push({ icon: Plus, label: `Track "${q.trim()}"`, run: () => actions.addKeyword(q.trim()), group: "Action", accent: true });
      dyn.push({ icon: Sparkle, label: `Ask AI: "${q.trim()}"`, run: () => actions.openCopilot(q.trim()), group: "AI", accent: true });
    }
    const ql = q.trim().toLowerCase();
    const filtered = ql ? base.filter((c) => c.label.toLowerCase().includes(ql)) : base;
    return [...dyn, ...filtered];
  }, [q, base, actions]);

  useEffect(() => { setActive(0); }, [q]);

  if (!open) return null;

  const exec = (item) => { item.run(); setOpen(false); };
  const onKeyDown = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(a + 1, items.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (e.key === "Enter" && items[active]) { e.preventDefault(); exec(items[active]); }
  };

  return (
    <>
      <div className="cmdk-scrim" onClick={() => setOpen(false)} />
      <div className="cmdk" role="dialog" aria-label="Command palette">
        <div className="cmdk-input">
          <Search size={18} />
          <input ref={inputRef} value={q} onChange={(e) => setQ(e.target.value)}
            onKeyDown={onKeyDown} placeholder="Track a keyword, ask AI, or jump anywhere…" />
          <span className="kbd">esc</span>
        </div>
        <div className="cmdk-list">
          {items.map((it, i) => {
            const Ic = it.icon;
            return (
              <div key={i} className={"cmdk-item" + (i === active ? " active" : "") + (it.accent ? " accent" : "")}
                onMouseEnter={() => setActive(i)} onClick={() => exec(it)}>
                <Ic size={16} />
                <span className="cmdk-label">{it.label}</span>
                <span className="cmdk-group">{it.group}</span>
              </div>
            );
          })}
          {items.length === 0 && <div className="cmdk-empty">No matches.</div>}
        </div>
        <div className="cmdk-foot">
          <span><span className="kbd">↑↓</span> navigate</span>
          <span><span className="kbd">↵</span> select</span>
          <span><Command size={11} /> K to toggle</span>
        </div>
      </div>
    </>
  );
}

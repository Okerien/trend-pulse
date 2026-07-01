import { useState } from "react";
import { useApp } from "./context/AppContext";
import { api } from "./lib/api";
import { reportUrl } from "./lib/urlState";

import FxStrip from "./components/FxStrip";
import TopBar from "./components/TopBar";
import KeywordInput from "./components/KeywordInput";
import KeywordGrid from "./components/KeywordGrid";
import ComparisonChart from "./components/ComparisonChart";
import CorrelationMatrix from "./components/CorrelationMatrix";
import NicheExplorer from "./components/NicheExplorer";
import DetailPanel from "./components/DetailPanel";
import WatchlistPanel from "./components/WatchlistPanel";
import InsightPanel from "./components/InsightPanel";
import ReportView from "./components/ReportView";
import ContentStudio from "./components/ContentStudio";
import CommandPalette from "./components/CommandPalette";
import CopilotRail from "./components/CopilotRail";
import { Bookmark, Search, Sparkle, Command } from "./components/Icons";

export default function App() {
  const app = useApp();
  const { report, keywords, range, geo, data } = app;

  const [tab, setTab] = useState("tracker");
  const [detail, setDetail] = useState(null);
  const [watchOpen, setWatchOpen] = useState(false);
  const [insight, setInsight] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [toast, setToast] = useState(null);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotQuery, setCopilotQuery] = useState(null);

  if (report) return <ReportView />;

  const openCopilot = (query) => { setCopilotQuery(query || null); setCopilotOpen(true); };
  const paletteActions = {
    setTab, setRange: app.setRange, setGeo: app.setGeo, toggleTheme: app.toggleTheme,
    addKeyword: app.addKeyword, openWatchlist: () => setWatchOpen(true),
    generateInsight: () => { setTab("tracker"); generate(); }, openCopilot,
  };

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(null), 2600);
  }

  async function generate() {
    if (!keywords.length) return;
    setGenerating(true);
    try {
      let correlations = [];
      try { correlations = (await api.correlate(keywords, range, geo)).pairs || []; } catch {}
      const payload = {
        keywords: data.keywords.map((k) => ({
          keyword: k.keyword,
          change_pct: k.change_pct,
          momentum: k.momentum,
          breakout: k.breakout,
          seasonality: k.seasonality,
          best_time: k.best_time,
        })),
        correlations,
      };
      const res = await api.summarise(payload);
      setInsight(res);
      if (!res.ok) showToast(res.summary);
    } catch {
      showToast("Couldn’t generate insight right now.");
    } finally {
      setGenerating(false);
    }
  }

  function openReport() {
    const client = window.prompt("Client name for the report (optional):", app.client || "");
    if (client === null) return;
    window.location.href = reportUrl({ keywords, range, geo, client });
  }

  return (
    <div className="app">
      <FxStrip />
      <TopBar onToggleReport={openReport} />

      <main className="main">
        <div className="container">
          <div className="tabs">
            <button className={tab === "tracker" ? "active" : ""} onClick={() => setTab("tracker")}>Keyword Tracker</button>
            <button className={tab === "niche" ? "active" : ""} onClick={() => setTab("niche")}>Niche Explorer</button>
            <button className={tab === "studio" ? "active" : ""} onClick={() => setTab("studio")}>Content Studio</button>
            <div style={{ flex: 1 }} />
            <button className="ghost-btn" onClick={() => setWatchOpen(true)}><Bookmark size={14} /> Watchlist</button>
          </div>

          {tab === "studio" ? (
            <ContentStudio onToast={showToast} />
          ) : tab === "tracker" ? (
            <>
              <KeywordInput />

              {keywords.length === 0 ? (
                <div className="empty">
                  <div className="ic"><Search size={26} /></div>
                  <h2>Add a keyword to begin</h2>
                  <p>Track unlimited keywords, compare momentum, and spot breakouts. Or explore a niche.</p>
                </div>
              ) : (
                <>
                  <div className="section-title">Tracked keywords</div>
                  <KeywordGrid onOpen={setDetail} />
                  <div style={{ height: 22 }} />
                  <ComparisonChart onGenerate={generate} generating={generating} onToast={showToast} />
                  <div style={{ height: 16 }} />
                  <InsightPanel insight={insight} />
                  <div style={{ height: 16 }} />
                  <CorrelationMatrix />
                </>
              )}
            </>
          ) : (
            <NicheExplorer />
          )}
        </div>
      </main>

      {detail && <DetailPanel keyword={detail} onClose={() => setDetail(null)} onAsk={openCopilot} />}
      {watchOpen && <WatchlistPanel onClose={() => setWatchOpen(false)} />}
      {toast && <div className="toast">{toast}</div>}

      <CommandPalette actions={paletteActions} />
      <CopilotRail open={copilotOpen} onClose={() => setCopilotOpen(false)}
        keywords={keywords} addKeyword={app.addKeyword}
        initialQuery={copilotQuery} onConsumeInitial={() => setCopilotQuery(null)} />

      {!copilotOpen && (
        <button className="copilot-fab" onClick={() => openCopilot()} title="AI Copilot (⌘K)">
          <Sparkle size={20} />
        </button>
      )}
    </div>
  );
}

import MomentumGauge from "./MomentumGauge";
import Sparkline from "./Sparkline";
import {
  Sparkle, Command, Compass, FileText, Search, ArrowRight, Bolt,
  Target, Globe, Check,
} from "./Icons";

// Sample series for the hero preview (real components, sample props — not a fake screenshot).
const SPARK = [22, 25, 24, 30, 34, 33, 40, 48, 52, 61, 68, 74, 82, 88];
const SPARK_DATES = SPARK.map((_, i) => `2026-04-${String(i + 1).padStart(2, "0")}`);

const PILLARS = [
  { ic: Target, title: "Keyword Tracker",
    body: "Track unlimited keywords with live momentum, breakout alerts, seasonality, and an AI read on every card.",
    accent: "var(--accent)" },
  { ic: Compass, title: "Niche Explorer",
    body: "Surface what's trending across eight niches — with AI-curated keywords when you need fresh ideas.",
    accent: "#0d9488" },
  { ic: FileText, title: "Content Studio",
    body: "Point it at a brand and its competitors. Get a 90-day content plan of briefs and social, timed to real trends.",
    accent: "#db2777" },
];

const AI_POINTS = [
  ["Inline AI reads", "Every keyword interpreted into one actionable line."],
  ["Grounded copilot", "Ask anything — get cited, real-time web answers."],
  ["⌘K everywhere", "Add, navigate, or ask AI from any screen instantly."],
  ["Content briefs", "Full outlines, keywords, and a calendar — written for you."],
];

export default function Landing({ onLaunch }) {
  return (
    <div className="landing">
      <nav className="lp-nav">
        <div className="container">
          <div className="logo">
            <span className="mark"><span /></span>
            Trend&nbsp;Pulse <small>by BendingWaters</small>
          </div>
          <div className="spacer" />
          <button className="ghost-btn accent" onClick={onLaunch}>
            Launch app <ArrowRight size={15} />
          </button>
        </div>
      </nav>

      {/* HERO */}
      <header className="lp-hero">
        <div className="container lp-hero-grid">
          <div className="lp-hero-copy">
            <div className="lp-eyebrow"><Sparkle size={13} /> Trend intelligence + AI content studio</div>
            <h1>Know what to publish<br />before your competitors do.</h1>
            <p>Live Google Trends, enriched with five free data sources and an AI layer that
              tells you what it means — and writes the plan.</p>
            <div className="lp-cta">
              <button className="ghost-btn accent lp-cta-main" onClick={onLaunch}>
                Launch Trend Pulse <ArrowRight size={16} />
              </button>
              <a className="ghost-btn" href="#how">See how it works</a>
            </div>
            <div className="lp-sources">
              <span>Powered by</span> Google Trends · Wikipedia · Reddit · News · Groq AI
            </div>
          </div>

          {/* Real-component preview card (not a fake screenshot) */}
          <div className="lp-preview">
            <div className="card lp-preview-card" style={{ "--accent": "var(--accent)" }}>
              <div className="kw-head">
                <div className="kw-name">ai agents</div>
                <span className="badge breakout"><Bolt size={11} /> Breakout</span>
              </div>
              <div className="score-row">
                <MomentumGauge value={87} band="green" />
                <div className="score-meta">
                  <div className="score-label">Momentum</div>
                  <div className="delta up">▲ 41%</div>
                </div>
              </div>
              <div className="ai-read"><Sparkle size={13} />
                <span>Breaking out with strong momentum and rising news — publish now to ride the surge.</span></div>
              <Sparkline dates={SPARK_DATES} values={SPARK} color="var(--accent)" />
            </div>
            <div className="lp-preview-glow" />
          </div>
        </div>
      </header>

      {/* PILLARS */}
      <section className="lp-section" id="how">
        <div className="container">
          <h2 className="lp-h2">Three tools. One intelligence layer.</h2>
          <div className="lp-pillars">
            {PILLARS.map((p) => (
              <div className="lp-pillar" key={p.title}>
                <div className="lp-pillar-ic" style={{ background: p.accent }}><p.ic size={20} /></div>
                <h3>{p.title}</h3>
                <p>{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI STRIP */}
      <section className="lp-ai">
        <div className="container lp-ai-grid">
          <div className="lp-ai-copy">
            <div className="lp-eyebrow"><Command size={13} /> AI-native, end to end</div>
            <h2 className="lp-h2" style={{ textAlign: "left", margin: "10px 0 14px" }}>
              An analyst built into every screen.</h2>
            <p className="lp-ai-lead">Not a chatbot bolted on. AI reads your data, explains
              trends with citations, suggests keywords, and drafts the content — right where you work.</p>
          </div>
          <div className="lp-ai-points">
            {AI_POINTS.map(([t, b]) => (
              <div className="lp-ai-point" key={t}>
                <span className="lp-check"><Check size={13} /></span>
                <div><b>{t}</b><span>{b}</span></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="lp-cta-band">
        <div className="container">
          <h2>Ready to see what's moving?</h2>
          <p>No setup. Add a keyword and the intelligence starts.</p>
          <button className="ghost-btn accent lp-cta-main" onClick={onLaunch}>
            Launch Trend Pulse <ArrowRight size={16} />
          </button>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="container">
          <div className="logo"><span className="mark"><span /></span> Trend&nbsp;Pulse</div>
          <span className="spacer" />
          <span className="lp-foot-note">Built for BendingWaters · $0 infrastructure</span>
        </div>
      </footer>
    </div>
  );
}

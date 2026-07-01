import { useMemo, useState } from "react";
import { useApp } from "../context/AppContext";
import DraftModal from "./DraftModal";
import { Sparkle, FileText, Calendar, Layers, Target, ArrowRight, Bolt, Plus } from "./Icons";

const band = (m) => (m >= 70 ? "green" : m >= 40 ? "amber" : "red");
const PLAT = { instagram: "Instagram", linkedin: "LinkedIn", x: "X", tiktok: "TikTok" };

export default function ContentPlan({ plan, intake, onReset, onToast }) {
  const { addKeyword } = useApp();
  const [view, setView] = useState("calendar");
  const [horizon, setHorizon] = useState(90);
  const [draft, setDraft] = useState(null);

  const articles = plan.articles || [];
  const social = plan.social || [];
  const fp = plan.footprint || {};
  const meta = plan.meta || {};

  const calendar = useMemo(() => {
    const today = new Date();
    const limit = new Date(today.getTime() + horizon * 86400000);
    const items = [
      ...articles.map((a) => ({ ...a, kind: "article" })),
      ...social.map((s) => ({ ...s, kind: "social" })),
    ].filter((i) => i.publish_date && new Date(i.publish_date) <= limit);
    items.sort((a, b) => new Date(a.publish_date) - new Date(b.publish_date));
    return items;
  }, [articles, social, horizon]);

  function exportCsv() {
    const rows = [["type", "date", "title_or_idea", "platform", "keyword", "why_now"]];
    articles.forEach((a) => rows.push(["article", a.publish_date || "", q(a.title), "", q(a.keyword), q(a.why_now)]));
    social.forEach((s) => rows.push(["social", s.publish_date || "", q(s.idea), s.platform || "", q(s.topic), q(s.why_now)]));
    const csv = rows.map((r) => r.join(",")).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `content-plan_${(intake.website || "brand").replace(/\W+/g, "-")}.csv`;
    a.click();
    onToast?.("Plan exported as CSV");
  }

  return (
    <div className="studio-result">
      <div className="panel insight" style={{ marginBottom: 16 }}>
        <div className="panel-head">
          <h3>Content strategy</h3>
          <span className="ai-badge">
            <Sparkle size={12} /> {plan.ai_generated ? "AI plan" : "Starter plan"}
          </span>
          <div className="spacer" />
          <button className="ghost-btn" onClick={exportCsv}>Export CSV</button>
          <button className="ghost-btn" onClick={onReset}>New analysis</button>
        </div>
        <p>{plan.summary}</p>
        <div className="footprint">
          <Stat label="Topics you cover" value={fp.you} />
          <Stat label="Competitors cover" value={fp.competitors_cover} />
          <Stat label="Opportunity gaps" value={fp.your_gaps} accent />
          <Stat label="Competitors read" value={meta.competitors_read} />
        </div>
        {!plan.ai_generated && (
          <div className="soft-note">AI model was unavailable, so this is a structured starter plan from the gap analysis. Re-run shortly for AI-written briefs.</div>
        )}
        {meta.competitors_unreadable?.length > 0 && (
          <div className="soft-note">Couldn’t read: {meta.competitors_unreadable.join(", ")} (they may block crawlers).</div>
        )}
      </div>

      <div className="seg">
        {[["calendar", "Calendar", Calendar], ["articles", "Articles", FileText],
          ["social", "Social", Layers], ["gaps", "Opportunities", Target]].map(([k, label, Ic]) => (
          <button key={k} className={view === k ? "on" : ""} onClick={() => setView(k)}>
            <Ic size={14} /> {label}
          </button>
        ))}
      </div>

      {view === "calendar" && (
        <div className="panel">
          <div className="panel-head">
            <h3>{horizon}-day calendar</h3>
            <div className="spacer" />
            <div className="pillstrip">
              <button className={horizon === 30 ? "active" : ""} onClick={() => setHorizon(30)}>30 days</button>
              <button className={horizon === 90 ? "active" : ""} onClick={() => setHorizon(90)}>90 days</button>
            </div>
          </div>
          <div className="cal-list">
            {calendar.map((it, i) => (
              <div className="cal-row" key={i}>
                <span className="cal-date num">{fmtDate(it.publish_date)}</span>
                <span className={"cal-kind " + it.kind}>{it.kind === "article" ? "Article" : PLAT[it.platform] || "Social"}</span>
                <span className="cal-title">{it.title || it.idea}</span>
                {it.breakout && <span className="badge breakout"><Bolt size={11} /> now</span>}
              </div>
            ))}
            {calendar.length === 0 && <p className="corr-note">No items scheduled in this window.</p>}
          </div>
        </div>
      )}

      {view === "articles" && (
        <div className="brief-grid">
          {articles.map((a, i) => (
            <div className="panel brief" key={i}>
              <div className="brief-head">
                <span className="num pubdate">{fmtDate(a.publish_date)}</span>
                {a.momentum != null && <span className={"badge metric"}><span className="k">mom</span> <span className="v">{a.momentum}</span></span>}
                {a.breakout && <span className="badge breakout"><Bolt size={11} /> Breakout</span>}
                <span className="badge">{a.format}</span>
              </div>
              <h4>{a.title}</h4>
              <p className="why"><b>Why now:</b> {a.why_now}</p>
              {a.angle && <p className="angle">{a.angle}</p>}
              {a.outline?.length > 0 && (
                <ul className="outline">{a.outline.map((h, j) => <li key={j}>{h}</li>)}</ul>
              )}
              <div className="brief-meta">
                {a.keyword && <span className="badge"><span className="k">keyword</span> {a.keyword}</span>}
                {a.word_target && <span className="badge num">{a.word_target}w</span>}
              </div>
              <button className="ghost-btn accent draft-btn" onClick={() => setDraft(a)}>
                <Sparkle size={13} /> Draft this
              </button>
            </div>
          ))}
        </div>
      )}

      {view === "social" && (
        <div className="brief-grid">
          {social.map((s, i) => (
            <div className="panel brief social" key={i}>
              <div className="brief-head">
                <span className="num pubdate">{fmtDate(s.publish_date)}</span>
                <span className="badge seasonal">{PLAT[s.platform] || s.platform}</span>
                <span className="badge">{s.format}</span>
              </div>
              <p className="social-idea">{s.idea}</p>
              {s.why_now && <p className="why"><b>Why now:</b> {s.why_now}</p>}
              <button className="ghost-btn accent draft-btn" onClick={() => setDraft(s)}>
                <Sparkle size={13} /> Draft this
              </button>
            </div>
          ))}
        </div>
      )}

      {view === "gaps" && (
        <div className="panel">
          <div className="panel-head"><h3>Opportunity map</h3></div>
          <div className="corr-list">
            {(plan.competitor_gaps || []).map((g, i) => (
              <div className="corr-row gap-row" key={i}>
                <span className={"score-mini " + band(g.momentum)}>{g.momentum}</span>
                <span className="corr-pair">{g.topic}</span>
                <span className="corr-note">covered by {g.covered_by}/{g.competitor_total} competitors · you don’t</span>
                <button className="add-chip" title="Track this keyword"
                  onClick={() => { addKeyword(g.topic); onToast?.(`Tracking "${g.topic}"`); }}>
                  <Plus size={12} /> Track
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {draft && <DraftModal item={draft} voice={intake.voice} onClose={() => setDraft(null)} onToast={onToast} />}
    </div>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div className={"fp-stat" + (accent ? " accent" : "")}>
      <div className="fp-val num">{value ?? "—"}</div>
      <div className="fp-label">{label}</div>
    </div>
  );
}
const q = (s) => { const v = String(s ?? ""); return /[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v; };
const fmtDate = (d) => d ? new Date(d).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "—";

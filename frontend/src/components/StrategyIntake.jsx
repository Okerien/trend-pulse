import { useState } from "react";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { Globe, Sparkle, Plus, Target } from "./Icons";

const GOALS = ["Brand awareness", "Leads & conversions", "SEO authority", "Social growth"];
const PLATFORMS = [
  ["instagram", "Instagram"], ["linkedin", "LinkedIn"], ["x", "X"], ["tiktok", "TikTok"],
];

export default function StrategyIntake({ onAnalyze }) {
  const { geo } = useApp();
  const [website, setWebsite] = useState("");
  const [what, setWhat] = useState("");
  const [goal, setGoal] = useState("SEO authority");
  const [competitors, setCompetitors] = useState(["", "", ""]);
  const [suggestions, setSuggestions] = useState([]);
  const [audience, setAudience] = useState("");
  const [voice, setVoice] = useState("");
  const [socials, setSocials] = useState("");
  const [platforms, setPlatforms] = useState(["instagram", "linkedin", "x", "tiktok"]);
  const [apw, setApw] = useState(2);
  const [spw, setSpw] = useState(5);
  const [suggesting, setSuggesting] = useState(false);

  const setComp = (i, v) => setCompetitors((c) => c.map((x, j) => (j === i ? v : x)));
  const togglePlatform = (p) =>
    setPlatforms((ps) => (ps.includes(p) ? ps.filter((x) => x !== p) : [...ps, p]));

  async function suggest() {
    if (!website && !what) return;
    setSuggesting(true);
    try {
      const r = await api.suggestCompetitors(website, what, geo);
      setSuggestions(r.suggestions || []);
    } catch { /* best-effort */ }
    setSuggesting(false);
  }

  function submit(e) {
    e.preventDefault();
    if (!website.trim() || !what.trim()) return;
    onAnalyze({
      website: website.trim(),
      what: what.trim(),
      niche: what.trim(),
      goal,
      geo,
      competitors: competitors.map((c) => c.trim()).filter(Boolean),
      audience: audience.trim(),
      voice: voice.trim(),
      socials: socials.trim(),
      platforms,
      cadence: { articles_per_week: apw, social_per_week: spw },
      scope_days: 90,
    });
  }

  const ready = website.trim() && what.trim();

  return (
    <form className="intake" onSubmit={submit}>
      <div className="intake-head">
        <div className="ic"><Target size={24} /></div>
        <div>
          <h2>Build a content system</h2>
          <p>We’ll read your site and your competitors, cross-reference live trends, and
            produce a 90-day plan of articles and social content. The more you share, the
            sharper the plan.</p>
        </div>
      </div>

      <div className="field-grid">
        <Field label="Website" required>
          <div className="with-icon"><Globe size={16} />
            <input value={website} onChange={(e) => setWebsite(e.target.value)}
              placeholder="yourbrand.com" />
          </div>
        </Field>
        <Field label="What do you do?" required>
          <input value={what} onChange={(e) => setWhat(e.target.value)}
            placeholder="e.g. organic skincare for African skin" />
        </Field>
      </div>

      <Field label="Primary goal">
        <div className="chips">
          {GOALS.map((g) => (
            <button type="button" key={g} className={"chip" + (goal === g ? " on" : "")}
              onClick={() => setGoal(g)}>{g}</button>
          ))}
        </div>
      </Field>

      <Field label="Competitors" hint="Up to 3 URLs — optional, but big quality lift">
        <div className="comp-rows">
          {competitors.map((c, i) => (
            <input key={i} value={c} onChange={(e) => setComp(i, e.target.value)}
              placeholder={`competitor ${i + 1} URL`} />
          ))}
        </div>
        <div className="suggest-row">
          <button type="button" className="ghost-btn" onClick={suggest} disabled={suggesting}>
            {suggesting ? <span className="spinner" /> : <Sparkle size={13} />} Suggest competitors
          </button>
          {suggestions.map((s, i) => (
            <span className="badge" key={i}>{s.name}</span>
          ))}
        </div>
      </Field>

      <div className="optional-note">Optional — the more you add, the better the output ↓</div>
      <div className="field-grid">
        <Field label="Target audience">
          <input value={audience} onChange={(e) => setAudience(e.target.value)}
            placeholder="e.g. women 25-40 in Lagos" />
        </Field>
        <Field label="Social handles">
          <input value={socials} onChange={(e) => setSocials(e.target.value)}
            placeholder="@yourbrand" />
        </Field>
      </div>

      <Field label="Brand voice" hint="A sentence, or paste a paragraph of your copy">
        <textarea className="note" value={voice} onChange={(e) => setVoice(e.target.value)}
          placeholder="warm, practical, a little playful…" />
      </Field>

      <Field label="Platforms">
        <div className="chips">
          {PLATFORMS.map(([k, label]) => (
            <button type="button" key={k}
              className={"chip" + (platforms.includes(k) ? " on" : "")}
              onClick={() => togglePlatform(k)}>{label}</button>
          ))}
        </div>
      </Field>

      <div className="field-grid">
        <Field label={`Articles / week: ${apw}`}>
          <input type="range" min="1" max="5" value={apw}
            onChange={(e) => setApw(+e.target.value)} />
        </Field>
        <Field label={`Social posts / week: ${spw}`}>
          <input type="range" min="1" max="14" value={spw}
            onChange={(e) => setSpw(+e.target.value)} />
        </Field>
      </div>

      <button className="ghost-btn accent intake-go" type="submit" disabled={!ready}>
        <Sparkle size={15} /> Build my content plan
      </button>
    </form>
  );
}

function Field({ label, hint, required, children }) {
  return (
    <div className="field-block">
      <label>{label}{required && <span className="req">*</span>}
        {hint && <span className="hint">{hint}</span>}</label>
      {children}
    </div>
  );
}

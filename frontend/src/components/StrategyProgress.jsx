import { Check, Target } from "./Icons";

const STAGES = [
  ["crawling_site", "Crawling your site"],
  ["reading_competitors", "Reading competitors"],
  ["scoring_trends", "Scoring trends"],
  ["writing_plan", "Writing your plan"],
];

export default function StrategyProgress({ status, error }) {
  const current = status?.stage || "queued";
  const order = STAGES.map((s) => s[0]);
  const idx = order.indexOf(current);

  return (
    <div className="progress-wrap">
      <div className="progress-card">
        <div className="ic spin-ic"><Target size={24} /></div>
        <h2>Building your content plan…</h2>
        <p>Reading the web and cross-referencing live trends. This takes up to a minute.</p>

        <div className="stage-list">
          {STAGES.map(([key, label], i) => {
            const done = error ? false : (status?.stage === "done" || i < idx);
            const active = !error && i === idx;
            return (
              <div className={"stage" + (done ? " done" : active ? " active" : "")} key={key}>
                <span className="stage-dot">{done ? <Check size={12} /> : active ? <span className="spinner" /> : i + 1}</span>
                {label}
              </div>
            );
          })}
        </div>

        {error ? (
          <p className="stage-error">Something went wrong ({error}). Please try again.</p>
        ) : (
          <div className="progress-bar"><span style={{ width: `${status?.progress || 5}%` }} /></div>
        )}
      </div>
    </div>
  );
}

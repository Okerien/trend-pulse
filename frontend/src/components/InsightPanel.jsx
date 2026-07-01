import { Sparkle } from "./Icons";

// Feature 23 — AI trend summary output.
export default function InsightPanel({ insight }) {
  if (!insight) return null;
  return (
    <div className="panel insight">
      <div className="panel-head">
        <h3>AI insight</h3>
        <div className="spacer" />
        <span className="ai-badge">
          <Sparkle size={12} /> {insight.model ? insight.model.split("/").pop() : "AI"}
        </span>
      </div>
      <p>{insight.summary}</p>
    </div>
  );
}

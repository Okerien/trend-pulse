import { useApp } from "../context/AppContext";

// Feature 22 — currency / market context strip + last-refreshed timestamp.
export default function FxStrip() {
  const { fx, refreshedAt, stale, demo, source } = useApp();
  const ngn = fx?.rates?.NGN;
  const zar = fx?.rates?.ZAR;
  return (
    <div className="fxstrip">
      <div className="container">
        <span><span className="lbl">USD / NGN</span> <b>{ngn ? `₦${ngn.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "—"}</b></span>
        <span><span className="lbl">USD / ZAR</span> <b>{zar ? `R${zar.toFixed(2)}` : "—"}</b></span>
        <span className="spacer" />
        {source === "wikipedia" ? (
          <span className="stale">Momentum via Wikipedia (Google Trends throttled)</span>
        ) : demo ? (
          <span className="stale">Sample data (Google Trends unavailable)</span>
        ) : stale ? (
          <span className="stale">Showing last known values</span>
        ) : (
          <span className="lbl" style={{ display: "inline-flex", alignItems: "center", gap: 7 }}>
            <span className="live-dot" /> Live
          </span>
        )}
        <span className="lbl">{refreshedAt ? `Updated ${refreshedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}</span>
      </div>
    </div>
  );
}

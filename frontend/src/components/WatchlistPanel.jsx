import { useApp } from "../context/AppContext";
import { setNote, togglePin } from "../lib/watchlist";
import { Close, Bolt, Bookmark } from "./Icons";

// Feature 20 — watchlist drawer with notes, current momentum + breakout.
export default function WatchlistPanel({ onClose }) {
  const { watchlist, setWatchlist, data, addKeyword } = useApp();
  const pins = Object.values(watchlist).sort((a, b) => b.addedAt - a.addedAt);

  const liveFor = (kw) =>
    data.keywords.find((k) => k.keyword.toLowerCase() === kw.toLowerCase());

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="drawer">
        <button className="iconbtn close" onClick={onClose}><Close size={18} /></button>
        <div className="drawer-inner">
          <h2>Watchlist</h2>
          <div className="corr-note">Pinned keywords + notes — saved on this device.</div>

          {pins.length === 0 ? (
            <p className="empty">Nothing pinned yet. Tap ☆ on any keyword card.</p>
          ) : (
            <div style={{ marginTop: 18, display: "flex", flexDirection: "column", gap: 14 }}>
              {pins.map((p) => {
                const live = liveFor(p.keyword);
                return (
                  <div className="panel" key={p.keyword} style={{ padding: 14 }}>
                    <div className="panel-head" style={{ marginBottom: 8 }}>
                      <strong>{p.keyword}</strong>
                      <div className="spacer" />
                      {live?.momentum != null && <span className="badge"><span className="k">Momentum</span> <span className="v">{live.momentum}</span></span>}
                      {live?.breakout && <span className="badge breakout"><Bolt size={11} /> Breakout</span>}
                      {!live && <button className="ghost-btn" onClick={() => addKeyword(p.keyword)}>Track</button>}
                      <button className="iconbtn on" title="Unpin"
                        onClick={() => setWatchlist((m) => togglePin(m, p.keyword))}><Bookmark filled size={15} /></button>
                    </div>
                    <textarea className="note" placeholder="Add a note — e.g. Q3 content target…"
                      defaultValue={p.note}
                      onBlur={(e) => setWatchlist((m) => setNote(m, p.keyword, e.target.value))} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

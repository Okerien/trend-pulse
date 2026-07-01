import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Close } from "./Icons";

// On-demand "Draft this" — expands a brief or social idea into full text.
export default function DraftModal({ item, voice, onClose, onToast }) {
  const [state, setState] = useState({ loading: true, text: "" });

  useEffect(() => {
    let alive = true;
    api.draft(item, voice)
      .then((r) => alive && setState({ loading: false, text: r.text || "", ok: r.ok }))
      .catch(() => alive && setState({ loading: false, text: "Drafting failed — try again.", ok: false }));
    return () => { alive = false; };
  }, [item, voice]);

  const title = item.title || `${item.platform || ""} ${item.format || "post"}`.trim();

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <div className="draft-modal">
        <div className="panel-head">
          <h3>{title}</h3>
          <div className="spacer" />
          {!state.loading && state.text && (
            <button className="ghost-btn" onClick={() => {
              navigator.clipboard?.writeText(state.text); onToast?.("Draft copied");
            }}>Copy</button>
          )}
          <button className="iconbtn" onClick={onClose}><Close size={18} /></button>
        </div>
        {state.loading ? (
          <div className="draft-loading"><span className="spinner" /> Writing your draft… (the free AI tier can be slow)</div>
        ) : (
          <pre className="draft-text">{state.text}</pre>
        )}
      </div>
    </>
  );
}

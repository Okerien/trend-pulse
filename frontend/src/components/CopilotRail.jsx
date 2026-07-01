import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { Sparkle, Send, Close, Link, Plus } from "./Icons";

// Persistent AI copilot — grounded, cited answers + keyword suggestions.
export default function CopilotRail({ open, onClose, keywords, addKeyword, initialQuery, onConsumeInitial }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const bodyRef = useRef(null);

  const ctx = keywords?.length ? keywords.join(", ") : "";

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  useEffect(() => {
    if (open && initialQuery) {
      send(initialQuery);
      onConsumeInitial?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialQuery]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    try {
      const r = await api.ai.ask(q, ctx);
      setMessages((m) => [...m, { role: "ai", text: r.answer, citations: r.citations || [] }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "I couldn't reach the web just now — try again." }]);
    }
    setBusy(false);
  }

  async function suggest() {
    const seed = keywords?.[0];
    if (!seed) { send("What keywords should I be tracking right now and why?"); return; }
    setMessages((m) => [...m, { role: "user", text: `Suggest keywords related to "${seed}"` }]);
    setBusy(true);
    try {
      const r = await api.ai.suggest(seed, 6);
      setMessages((m) => [...m, { role: "ai", text: r.keywords?.length ? "Here are keywords worth tracking — tap to add:" : "No suggestions right now.", chips: r.keywords || [] }]);
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "Couldn't fetch suggestions." }]);
    }
    setBusy(false);
  }

  if (!open) return null;

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="copilot">
        <div className="copilot-head">
          <div className="copilot-title"><span className="copilot-ic"><Sparkle size={15} /></span> AI Copilot</div>
          <button className="iconbtn" onClick={onClose}><Close size={18} /></button>
        </div>

        <div className="copilot-body" ref={bodyRef}>
          {messages.length === 0 && (
            <div className="copilot-welcome">
              <p>Ask anything about your trends — answers are grounded in live web sources with citations.</p>
              <div className="copilot-quick">
                <button onClick={() => send("What's driving search interest in my tracked keywords right now?")} disabled={!ctx}>Why are my keywords trending?</button>
                <button onClick={suggest}>Suggest keywords to track</button>
                <button onClick={() => send("What are the biggest emerging marketing trends this month?")}>Emerging trends this month</button>
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={"msg " + m.role}>
              {m.role === "ai" && <span className="msg-ic"><Sparkle size={13} /></span>}
              <div className="msg-bubble">
                <div className="msg-text">{m.text}</div>
                {m.chips?.length > 0 && (
                  <div className="msg-chips">
                    {m.chips.map((c, j) => (
                      <button key={j} className="add-chip" onClick={() => addKeyword(c)}>
                        <Plus size={12} /> {c}
                      </button>
                    ))}
                  </div>
                )}
                {m.citations?.length > 0 && (
                  <div className="msg-cites">
                    {m.citations.map((c) => (
                      <a key={c.n} href={c.url} target="_blank" rel="noreferrer" title={c.title}>
                        <Link size={11} /> {c.n}. {hostname(c.url)}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && <div className="msg ai"><span className="msg-ic"><Sparkle size={13} /></span><div className="msg-bubble"><span className="typing"><i /><i /><i /></span></div></div>}
        </div>

        <form className="copilot-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the copilot…" />
          <button type="submit" className="ghost-btn accent" disabled={busy || !input.trim()}><Send size={15} /></button>
        </form>
      </aside>
    </>
  );
}

const hostname = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return "source"; } };

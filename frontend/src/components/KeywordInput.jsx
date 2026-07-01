import { useEffect, useRef, useState } from "react";
import { useApp } from "../context/AppContext";
import { api } from "../lib/api";
import { Search, Plus, Sparkle } from "./Icons";

// Feature 1 — add keywords + live AI suggestions as you type.
export default function KeywordInput() {
  const { addKeyword } = useApp();
  const [val, setVal] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const timer = useRef(null);
  const boxRef = useRef(null);

  // Debounced AI suggestions.
  useEffect(() => {
    clearTimeout(timer.current);
    const q = val.trim();
    if (q.length < 3) { setSuggestions([]); return; }
    timer.current = setTimeout(() => {
      setLoading(true);
      api.ai.suggest(q, 5)
        .then((r) => { setSuggestions(r.keywords || []); setOpen(true); })
        .catch(() => setSuggestions([]))
        .finally(() => setLoading(false));
    }, 450);
    return () => clearTimeout(timer.current);
  }, [val]);

  useEffect(() => {
    const onDoc = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  function add(kw) {
    const parts = kw.split(",").map((s) => s.trim()).filter(Boolean);
    parts.forEach(addKeyword);
    setVal(""); setSuggestions([]); setOpen(false);
  }

  return (
    <div className="kwinput-wrap" ref={boxRef}>
      <form className="kwinput" onSubmit={(e) => { e.preventDefault(); add(val); }}>
        <div className="field">
          <Search size={16} />
          <input
            value={val}
            onChange={(e) => setVal(e.target.value)}
            onFocus={() => suggestions.length && setOpen(true)}
            placeholder="Add a keyword to track — e.g. organic skincare, jollof rice…"
            aria-label="Add keyword"
          />
          {loading && <span className="kw-spin"><span className="spinner" /></span>}
        </div>
        <button className="ghost-btn accent" type="submit"><Plus size={15} /> Track</button>
      </form>

      {open && suggestions.length > 0 && (
        <div className="kw-suggest">
          <div className="kw-suggest-head"><Sparkle size={12} /> AI suggestions</div>
          {suggestions.map((s, i) => (
            <button key={i} className="kw-suggest-item" onClick={() => add(s)}>
              <Plus size={13} /> {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

import { useEffect, useLayoutEffect, useState } from "react";
import { Sparkle, ArrowRight, Close } from "./Icons";

// First-run guided walkthrough. Spotlights real UI elements with a tooltip.
const STEPS = [
  { target: null, title: "Welcome to Trend Pulse",
    body: "A 60-second tour of the essentials. You can skip anytime." },
  { target: ".kwinput", title: "Start with a keyword",
    body: "Add anything to track. AI suggests related keywords as you type, and every card gets a live read." },
  { target: ".tabs", title: "Three modes",
    body: "Keyword Tracker, Niche Explorer, and the AI Content Studio that writes full content plans.", placement: "bottom" },
  { target: ".cmdk-trigger", title: "⌘K — your fast path",
    body: "Press ⌘K (or Ctrl+K) anywhere to add keywords, jump around, or ask the AI.", placement: "bottom" },
  { target: ".copilot-fab", title: "Ask the AI copilot",
    body: "Grounded, cited answers on any trend or market question — powered by live web search.", placement: "left" },
  { target: null, title: "You're set",
    body: "Add your first keyword and the intelligence starts. Everything's live." },
];

export default function Tour({ onDone }) {
  const [i, setI] = useState(0);
  const [rect, setRect] = useState(null);
  const step = STEPS[i];

  useLayoutEffect(() => {
    if (!step.target) { setRect(null); return; }
    const el = document.querySelector(step.target);
    if (!el) { setRect(null); return; }
    el.scrollIntoView({ block: "center", behavior: "smooth" });
    const measure = () => setRect(el.getBoundingClientRect());
    measure();
    window.addEventListener("resize", measure);
    const t = setTimeout(measure, 260); // after scroll settles
    return () => { window.removeEventListener("resize", measure); clearTimeout(t); };
  }, [i]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onDone();
      if (e.key === "ArrowRight" || e.key === "Enter") next();
      if (e.key === "ArrowLeft") setI((n) => Math.max(0, n - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const next = () => (i >= STEPS.length - 1 ? onDone() : setI(i + 1));

  const pad = 8;
  const spot = rect && {
    top: rect.top - pad, left: rect.left - pad,
    width: rect.width + pad * 2, height: rect.height + pad * 2,
  };
  const tip = tipPosition(rect, step.placement);

  return (
    <div className="tour">
      {spot ? (
        <div className="tour-spot" style={spot} />
      ) : (
        <div className="tour-dim" />
      )}

      <div className={"tour-tip" + (rect ? "" : " center")} style={tip}>
        <div className="tour-tip-head">
          <Sparkle size={14} />
          <span className="tour-count">{i + 1} / {STEPS.length}</span>
          <button className="iconbtn" onClick={onDone} aria-label="Skip"><Close size={16} /></button>
        </div>
        <h4>{step.title}</h4>
        <p>{step.body}</p>
        <div className="tour-actions">
          <button className="tour-skip" onClick={onDone}>Skip tour</button>
          <div className="spacer" />
          {i > 0 && <button className="ghost-btn" onClick={() => setI(i - 1)}>Back</button>}
          <button className="ghost-btn accent" onClick={next}>
            {i >= STEPS.length - 1 ? "Get started" : <>Next <ArrowRight size={14} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}

function tipPosition(rect, placement) {
  const W = 320, vw = window.innerWidth, vh = window.innerHeight;
  if (!rect) return { top: "50%", left: "50%", transform: "translate(-50%,-50%)" };
  let top, left;
  if (placement === "left") {
    top = Math.min(rect.top, vh - 220);
    left = Math.max(16, rect.left - W - 16);
  } else if (placement === "bottom" || rect.top < vh / 2) {
    top = rect.bottom + 14;
    left = Math.min(Math.max(16, rect.left), vw - W - 16);
  } else {
    top = Math.max(16, rect.top - 200);
    left = Math.min(Math.max(16, rect.left), vw - W - 16);
  }
  return { top, left, width: W };
}

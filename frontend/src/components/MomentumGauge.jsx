import { useEffect, useRef, useState } from "react";

// Live animated radial momentum gauge — the arc sweeps to the value and the
// number counts up on mount. Colour follows the band.
export default function MomentumGauge({ value = 0, band = "amber", size = 76 }) {
  const [shown, setShown] = useState(0);
  const raf = useRef(0);
  const r = (size - 9) / 2;
  const circ = 2 * Math.PI * r;
  const color = `var(--${band})`;

  useEffect(() => {
    const start = performance.now();
    const from = shown;
    const dur = 900;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      setShown(Math.round(from + (value - from) * eased));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  const offset = circ * (1 - shown / 100);

  return (
    <div className="gauge" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="var(--surface-2)" strokeWidth="7" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth="7" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ filter: `drop-shadow(0 0 5px ${color})`, transition: "stroke .3s" }} />
      </svg>
      <div className="gauge-num">
        <span className={"num " + band}>{shown}</span>
      </div>
    </div>
  );
}

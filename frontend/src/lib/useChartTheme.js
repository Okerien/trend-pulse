import { useMemo } from "react";
import { useApp } from "../context/AppContext";

// Reads the resolved CSS variables so Recharts (which needs concrete colors,
// not CSS vars) follows light/dark automatically.
export function useChartTheme() {
  const { theme } = useApp();
  return useMemo(() => {
    const cs = getComputedStyle(document.documentElement);
    const v = (n, fallback) => cs.getPropertyValue(n).trim() || fallback;
    return {
      grid: v("--grid-line", "#eee"),
      tick: v("--tick", "#999"),
      surface: v("--surface", "#fff"),
      border: v("--border", "#e5e5e5"),
      text: v("--text", "#111"),
      faint: v("--text-faint", "#999"),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme]);
}

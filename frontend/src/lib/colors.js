// Feature 1 — a curated, colourblind-aware palette of 12 distinct hues.
// Colours are assigned in order and persisted per keyword so they stay stable
// across sessions and shared links.
export const PALETTE = [
  "#2563eb", // blue
  "#dc2626", // red
  "#16a34a", // green
  "#d97706", // amber
  "#7c3aed", // violet
  "#0891b2", // cyan
  "#db2777", // pink
  "#65a30d", // lime
  "#ea580c", // orange
  "#4f46e5", // indigo
  "#0d9488", // teal
  "#9333ea", // purple
];

// Deterministic colour for a keyword given the current ordered list of keywords,
// so the same set always yields the same colours (important for shared views).
export function colorFor(keyword, orderedKeywords) {
  const idx = orderedKeywords.findIndex(
    (k) => k.toLowerCase() === keyword.toLowerCase()
  );
  return PALETTE[(idx < 0 ? 0 : idx) % PALETTE.length];
}

// A muted version of a colour (used for the Wikipedia overlay line, Feature 9).
export function muted(hex) {
  return hex + "66"; // ~40% alpha
}

// Feature 20 — watchlist + notes, persisted in localStorage so it survives sessions.
const KEY = "trendpulse.watchlist.v1";

export function loadWatchlist() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || {};
  } catch {
    return {};
  }
}

export function saveWatchlist(map) {
  localStorage.setItem(KEY, JSON.stringify(map));
}

// map shape: { "<lowercased keyword>": { keyword, note, addedAt } }
export function togglePin(map, keyword) {
  const k = keyword.toLowerCase();
  const next = { ...map };
  if (next[k]) delete next[k];
  else next[k] = { keyword, note: "", addedAt: Date.now() };
  saveWatchlist(next);
  return next;
}

export function setNote(map, keyword, note) {
  const k = keyword.toLowerCase();
  if (!map[k]) return map;
  const next = { ...map, [k]: { ...map[k], note } };
  saveWatchlist(next);
  return next;
}

export function isPinned(map, keyword) {
  return Boolean(map[keyword.toLowerCase()]);
}

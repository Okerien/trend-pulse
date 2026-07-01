import { createContext, useContext, useEffect, useState, useCallback, useRef } from "react";
import { api } from "../lib/api";
import { readState, syncUrl } from "../lib/urlState";
import { loadWatchlist } from "../lib/watchlist";

const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

const initial = readState();

export function AppProvider({ children }) {
  const [keywords, setKeywords] = useState(initial.keywords);
  const [range, setRange] = useState(initial.range);
  const [geo, setGeo] = useState(initial.geo);
  const [report] = useState(initial.report);
  const [client] = useState(initial.client);

  const [data, setData] = useState({ dates: [], keywords: [] });
  const [fx, setFx] = useState(null);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stale, setStale] = useState(false);
  const [demo, setDemo] = useState(false);
  const [source, setSource] = useState("google");
  const [watchlist, setWatchlist] = useState(loadWatchlist());
  const [theme, setThemeState] = useState(
    () => document.documentElement.dataset.theme || "light"
  );

  const setTheme = useCallback((t) => {
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem("trendpulse.theme", t); } catch {}
    setThemeState(t);
  }, []);
  const toggleTheme = useCallback(
    () => setTheme(theme === "dark" ? "light" : "dark"),
    [theme, setTheme]
  );

  const reqId = useRef(0);

  const fetchTrends = useCallback(async () => {
    if (keywords.length === 0) {
      setData({ dates: [], keywords: [] });
      return;
    }
    const id = ++reqId.current;
    setLoading(true);
    try {
      const res = await api.trends(keywords, range, geo);
      if (id !== reqId.current) return; // a newer request superseded this one
      setData({ dates: res.dates || [], keywords: res.keywords || [] });
      setStale(Boolean(res.stale));
      setDemo(Boolean(res.demo));
      setSource(res.source || "google");
      if (res.fx) setFx(res.fx);
      setRefreshedAt(new Date());
    } catch (e) {
      if (id === reqId.current) setStale(true);
    } finally {
      if (id === reqId.current) setLoading(false);
    }
  }, [keywords, range, geo]);

  useEffect(() => {
    fetchTrends();
    syncUrl({ keywords, range, geo });
  }, [fetchTrends, keywords, range, geo]);

  // Currency strip (Feature 22) — independent refresh.
  useEffect(() => {
    let alive = true;
    api.context()
      .then((c) => alive && (setFx(c.fx), setRefreshedAt(new Date())))
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  const addKeyword = useCallback((kw) => {
    const clean = kw.trim();
    if (!clean) return;
    setKeywords((prev) =>
      prev.some((k) => k.toLowerCase() === clean.toLowerCase()) ? prev : [...prev, clean]
    );
  }, []);

  const removeKeyword = useCallback((kw) => {
    setKeywords((prev) => prev.filter((k) => k.toLowerCase() !== kw.toLowerCase()));
  }, []);

  const value = {
    keywords, range, geo, report, client,
    data, fx, refreshedAt, loading, stale, demo, source,
    watchlist, setWatchlist,
    theme, toggleTheme,
    setRange, setGeo, addKeyword, removeKeyword,
    refresh: fetchTrends,
  };
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

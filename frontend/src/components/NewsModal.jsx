import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Close, External } from "./Icons";

// News drill-down — the actual recent articles behind the News badge.
export default function NewsModal({ keyword, onClose }) {
  const [state, setState] = useState({ loading: true, articles: [] });

  useEffect(() => {
    let alive = true;
    api.news(keyword)
      .then((r) => alive && setState({ loading: false, articles: r.articles || [] }))
      .catch(() => alive && setState({ loading: false, articles: [] }));
    return () => { alive = false; };
  }, [keyword]);

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <div className="news-modal">
        <div className="panel-head">
          <h3>News · {keyword}</h3>
          <div className="spacer" />
          <button className="iconbtn" onClick={onClose}><Close size={18} /></button>
        </div>
        {state.loading ? (
          <div className="draft-loading"><span className="spinner" /> Loading articles…</div>
        ) : state.articles.length === 0 ? (
          <p className="corr-note">No recent articles found.</p>
        ) : (
          <div className="news-list">
            {state.articles.map((a, i) => (
              <a className="news-item" key={i} href={a.url} target="_blank" rel="noreferrer">
                <div className="news-title">{a.title}</div>
                <div className="news-meta">
                  <span>{a.source}</span>
                  {a.publishedAt && <span className="num">{new Date(a.publishedAt).toLocaleDateString()}</span>}
                  <External size={12} />
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

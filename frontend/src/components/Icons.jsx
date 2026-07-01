// Minimal, consistent stroke-1.6 icon set (currentColor). Replaces emoji so the
// UI reads like a data product, not a chat. One family, one weight.
const S = ({ children, size = 16, fill = "none" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill}
    stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    {children}
  </svg>
);

export const Search = (p) => <S {...p}><circle cx="11" cy="11" r="7" /><path d="m20 20-3.2-3.2" /></S>;
export const Sun = (p) => <S {...p}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></S>;
export const Moon = (p) => <S {...p}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" /></S>;
export const Plus = (p) => <S {...p}><path d="M12 5v14M5 12h14" /></S>;
export const Close = (p) => <S {...p}><path d="M6 6l12 12M18 6 6 18" /></S>;
export const Sparkle = (p) => <S {...p}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /></S>;
export const Refresh = (p) => <S {...p}><path d="M21 12a9 9 0 1 1-2.6-6.4M21 4v4h-4" /></S>;
export const External = (p) => <S {...p}><path d="M14 4h6v6M20 4l-9 9M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" /></S>;
export const Calendar = (p) => <S {...p}><rect x="3" y="4.5" width="18" height="16" rx="2.5" /><path d="M3 9h18M8 2.5v4M16 2.5v4" /></S>;
export const Bolt = (p) => <S {...p} fill="currentColor" stroke="none"><path d="M13 2 4.5 13.5H11l-1 8.5L19 10h-6.5L13 2Z" /></S>;
export const Bookmark = ({ filled, ...p }) => <S {...p} fill={filled ? "currentColor" : "none"}><path d="M6 3.5h12a1 1 0 0 1 1 1V21l-7-4-7 4V4.5a1 1 0 0 1 1-1Z" /></S>;
export const ArrowDown = (p) => <S {...p}><path d="M12 5v14M6 13l6 6 6-6" /></S>;
export const Image = (p) => <S {...p}><rect x="3" y="4" width="18" height="16" rx="2.5" /><circle cx="8.5" cy="9.5" r="1.5" /><path d="m4 18 5-5 4 4 3-3 4 4" /></S>;
export const Globe = (p) => <S {...p}><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z" /></S>;
export const FileText = (p) => <S {...p}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h6" /></S>;
export const Trash = (p) => <S {...p}><path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13" /></S>;
export const ArrowRight = (p) => <S {...p}><path d="M5 12h14M13 6l6 6-6 6" /></S>;
export const Target = (p) => <S {...p}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.4" fill="currentColor" /></S>;
export const Layers = (p) => <S {...p}><path d="M12 3 3 8l9 5 9-5-9-5ZM3 13l9 5 9-5M3 17l9 5 9-5" /></S>;
export const Check = (p) => <S {...p}><path d="M5 12.5 10 17l9-10" /></S>;
export const Command = (p) => <S {...p}><path d="M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3z" /></S>;
export const Send = (p) => <S {...p}><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" /></S>;
export const Link = (p) => <S {...p}><path d="M9 15l6-6M10.5 6.5l1-1a4 4 0 0 1 6 6l-1 1M13.5 17.5l-1 1a4 4 0 0 1-6-6l1-1" /></S>;
export const Compass = (p) => <S {...p}><circle cx="12" cy="12" r="9" /><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" /></S>;

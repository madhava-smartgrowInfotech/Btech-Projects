// Server timestamps are naive local time (no zone suffix), so `new Date()` reads them as local too.
const toDate = (s: string) => new Date(s);

export const fmtDate = (s?: string | null) =>
  s ? toDate(s).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "-";
export const fmtDay = (s?: string | null) =>
  s ? toDate(s).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "-";
export const pct = (v: number | null | undefined) => (v === null || v === undefined ? "-" : `${Math.round(v * 1000) / 10}%`);
export const days = (v: number | null | undefined) =>
  v === null || v === undefined ? "-" : v < 1 ? `${Math.round(v * 24)} h` : `${Math.round(v * 10) / 10} d`;

export function timeAgo(s: string) {
  const d = (Date.now() - toDate(s).getTime()) / 1000;
  if (d < 60) return "just now";
  if (d < 3600) return `${Math.floor(d / 60)} min ago`;
  if (d < 86400) return `${Math.floor(d / 3600)} h ago`;
  return `${Math.floor(d / 86400)} d ago`;
}

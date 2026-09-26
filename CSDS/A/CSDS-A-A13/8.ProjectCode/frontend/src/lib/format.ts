const dateFmt = new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
const shortDateFmt = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short" });
const dateTimeFmt = new Intl.DateTimeFormat(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
const numberFmt = new Intl.NumberFormat();

/** Parse an ISO date ("2026-10-05") as a local calendar date. */
export function parseDate(value: string) {
  const [y, m, d] = value.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Server timestamps are UTC without a zone suffix. */
export function parseTimestamp(value: string) {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
}

export const formatDate = (value: string) => dateFmt.format(parseDate(value));
export const formatShortDate = (value: string) => shortDateFmt.format(parseDate(value));
export const formatDateTime = (value: string) => dateTimeFmt.format(parseTimestamp(value));
export const formatNumber = (value: number) => numberFmt.format(value);
export const formatTime = (value: string) => value.slice(0, 5);
export const formatPercent = (value: number, digits = 0) => `${(value * 100).toFixed(digits)}%`;

export function formatDuration(ms: number) {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(ms < 10_000 ? 1 : 0)} s`;
}

export function timeAgo(value: string) {
  const seconds = Math.round((Date.now() - parseTimestamp(value).getTime()) / 1000);
  if (seconds < 45) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return formatDateTime(value);
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join("");
}

export function plural(count: number, one: string, many = `${one}s`) {
  return `${formatNumber(count)} ${count === 1 ? one : many}`;
}

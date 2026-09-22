const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const inrWhole = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 });

export function formatINR(value: number, whole = false) {
  if (!Number.isFinite(value)) return "₹0";
  return (whole || Number.isInteger(value) ? inrWhole : inr).format(value);
}

export function formatCompact(value: number) {
  return compact.format(value);
}

export function formatPercent(value: number, digits = 1) {
  return `${(value * 100).toFixed(digits)}%`;
}

const localeFor = (lang: string) => (lang === "hi" ? "hi-IN" : lang === "te" ? "te-IN" : "en-IN");

export function formatDateTime(iso: string, lang = "en") {
  return new Intl.DateTimeFormat(localeFor(lang), { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }).format(
    new Date(iso),
  );
}

export function formatDate(iso: string, lang = "en") {
  return new Intl.DateTimeFormat(localeFor(lang), { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export function formatTime(iso: string, lang = "en") {
  return new Intl.DateTimeFormat(localeFor(lang), { hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export function formatCountdown(ms: number) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

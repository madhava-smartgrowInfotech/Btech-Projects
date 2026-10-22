import { useMemo } from "react";

import { useAuth } from "@/lib/auth";

const LOCALES: Record<string, string> = { INR: "en-IN", USD: "en-US", EUR: "de-DE", GBP: "en-GB" };

export interface Money {
  /** Whole-unit amount: ₹1,23,456 */
  (value: number | null | undefined): string;
  /** With paise: ₹1,234.50 */
  exact: (value: number | null | undefined) => string;
  /** Short axis labels: ₹65K */
  compact: (value: number) => string;
  currency: string;
  symbol: string;
}

export function makeMoney(currency = "INR"): Money {
  const locale = LOCALES[currency] ?? "en-IN";
  const whole = new Intl.NumberFormat(locale, { style: "currency", currency, maximumFractionDigits: 0 });
  const exact = new Intl.NumberFormat(locale, { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const compact = new Intl.NumberFormat(locale, { style: "currency", currency, notation: "compact", maximumFractionDigits: 1 });
  const guard = (v: number | null | undefined) => v === null || v === undefined || Number.isNaN(v);
  const fn = ((v) => (guard(v) ? "-" : whole.format(v as number))) as Money;
  fn.exact = (v) => (guard(v) ? "-" : exact.format(v as number));
  // Explicit units: some ICU builds print "T" for thousand in en-IN, which reads as trillion.
  fn.compact = (v) => {
    if (currency !== "INR") return compact.format(v);
    const abs = Math.abs(v);
    const sign = v < 0 ? "-" : "";
    const trim = (n: number) => String(Math.round(n * 10) / 10);
    if (abs >= 1e7) return `${sign}₹${trim(abs / 1e7)}Cr`;
    if (abs >= 1e5) return `${sign}₹${trim(abs / 1e5)}L`;
    if (abs >= 1e3) return `${sign}₹${trim(abs / 1e3)}K`;
    return `${sign}₹${Math.round(abs)}`;
  };
  fn.currency = currency;
  fn.symbol = whole.formatToParts(0).find((p) => p.type === "currency")?.value ?? currency;
  return fn;
}

/** Formatter bound to the signed-in user's preferred currency. */
export function useMoney(): Money {
  const { user } = useAuth();
  const currency = user?.currency ?? "INR";
  return useMemo(() => makeMoney(currency), [currency]);
}

export const pct = (n: number | null | undefined, digits = 0) =>
  n === null || n === undefined || Number.isNaN(n) ? "-" : `${n.toFixed(digits)}%`;

export function todayISO() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export function addDaysISO(iso: string, days: number) {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + days);
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export function monthLabel(ym: string) {
  const [y, m] = ym.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleString("en-IN", { month: "short", year: "2-digit" });
}

export const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export const humanize = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

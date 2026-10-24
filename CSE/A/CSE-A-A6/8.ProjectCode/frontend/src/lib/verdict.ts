import type { BadgeTone } from "@/components/ui/Badge";

/** The three outputs of the rule engine -> one consistent tone everywhere (icon + text always accompany color). */
export function verdictTone(state: string): BadgeTone {
  if (state === "Normal") return "success";
  if (state.startsWith("Possible")) return "danger";
  return "warning";
}

export const fixed = (v: number | null | undefined, digits = 3) => (v === null || v === undefined ? "-" : v.toFixed(digits));

/** UTC ISO timestamp -> "24 Oct 2026, 10:42:07 UTC". */
export function utcStamp(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return (
    d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "UTC" }) +
    " UTC"
  );
}

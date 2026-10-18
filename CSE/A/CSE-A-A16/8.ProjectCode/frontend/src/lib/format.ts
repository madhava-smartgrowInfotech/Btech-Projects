export const pct = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined || Number.isNaN(v) ? "-" : `${(v * 100).toFixed(digits)}%`;

export const num = (v: number | null | undefined) => (v === null || v === undefined ? "-" : v.toLocaleString("en-US"));

/** Epoch seconds -> "18 Oct 2026, 10:42". */
export function whenTrained(epochSeconds: number | null | undefined) {
  if (!epochSeconds) return "-";
  return new Date(epochSeconds * 1000).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Spoken names for the control classes, letters unchanged. */
export const classLabel = (c: string) => (c === "space" ? "Space" : c === "del" ? "Delete" : c === "nothing" ? "Nothing" : c);

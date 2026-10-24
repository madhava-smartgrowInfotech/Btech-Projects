import type { BadgeTone } from "@/components/ui/Badge";
import type { Severity } from "@/lib/api";

export const SEVERITY_TONE: Record<Severity, BadgeTone> = {
  high: "danger",
  medium: "warning",
  low: "info",
  none: "success",
};

export const SEVERITY_LABEL: Record<Severity, string> = {
  high: "High severity",
  medium: "Medium severity",
  low: "Low severity",
  none: "Healthy",
};

export const SEVERITY_COLOR: Record<Severity, string> = {
  high: "#FB7185",
  medium: "#FBBF24",
  low: "#60A5FA",
  none: "#34D399",
};

export const TREATMENT_TONE: Record<string, BadgeTone> = {
  chemical: "danger",
  organic: "success",
  cultural: "info",
};

export const pct = (n: number, digits = 1) => `${(n * 100).toFixed(digits)}%`;

/** "Corn (Maize)" -> "corn", used to pre-select the crop on the detect screen. */
export function cropKey(crop: string): string {
  const k = crop.toLowerCase().split(/[ (,]/)[0];
  return k === "pepper" || k === "bell" ? "pepper" : k;
}

import type { BadgeTone } from "@/components/ui/Badge";
import type { Stage } from "@/lib/types";

export const STAGE_TONE: Record<Stage, BadgeTone> = {
  Low: "success",
  Moderate: "warning",
  High: "magenta",
  "Very high": "danger",
};

/** Bar colour for a probability: the same thresholds the previous build used (75 / 50 / 30). */
export function probFill(value: number | null | undefined): string {
  const v = (value ?? 0) * 100;
  if (v >= 75) return "bg-danger";
  if (v >= 50) return "bg-magenta";
  if (v >= 30) return "bg-warning";
  return "bg-success";
}

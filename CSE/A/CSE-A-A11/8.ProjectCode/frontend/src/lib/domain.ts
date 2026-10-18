import type { BadgeTone } from "@/components/ui/Badge";
import type { Severity, Verdict } from "@/lib/types";

export const SEV_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];
export const SEV_RANK: Record<Severity, number> = { critical: 4, high: 3, medium: 2, low: 1, info: 0 };
export const SEV_TONE: Record<Severity, BadgeTone> = { critical: "violet", high: "danger", medium: "warning", low: "cyan", info: "neutral" };
export const SEV_COLOR: Record<Severity, string> = {
  critical: "#A78BFA",
  high: "#FB7185",
  medium: "#FBBF24",
  low: "#22D3EE",
  info: "#94A3B8",
};

export const VERDICT_INFO: Record<Verdict, { title: string; sub: string; tone: "danger" | "warning" | "success" }> = {
  BLOCK: { title: "Merge blocked", sub: "High-impact security issues were introduced by this change.", tone: "danger" },
  REQUEST_CHANGES: { title: "Changes requested", sub: "Issues worth fixing before merge were found.", tone: "warning" },
  APPROVE: { title: "Safe to merge", sub: "No blocking issues were found in the changed code.", tone: "success" },
};

export const verdictLabel = (v: Verdict) => v.replace("_", " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

export function riskColor(score: number) {
  return score < 30 ? "#34D399" : score < 70 ? "#FBBF24" : "#FB7185";
}

export const titleCase = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export const pct = (n: number, digits = 0) => `${(n * 100).toFixed(digits)}%`;

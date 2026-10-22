import { CircleAlert, ShieldAlert, ShieldCheck, type LucideIcon } from "lucide-react";

import type { BadgeTone } from "@/components/ui/Badge";
import type { Label } from "@/lib/api";

/** One place that decides how each verdict looks, so color is never the only signal (icon + text always travel with it). */
export const VERDICT: Record<Label, { tone: BadgeTone; color: string; icon: LucideIcon; meaning: string }> = {
  REAL: {
    tone: "success",
    color: "#34D399",
    icon: ShieldCheck,
    meaning: "Written like reliable reporting: sourced, verified and measured in tone.",
  },
  "PARTIALLY TRUE": {
    tone: "warning",
    color: "#FBBF24",
    icon: CircleAlert,
    meaning: "Mixes verified facts with unverified or exaggerated claims. Check the flagged phrases.",
  },
  FAKE: {
    tone: "danger",
    color: "#FB7185",
    icon: ShieldAlert,
    meaning: "Shows the style of fabricated or clickbait content: sensational, secretive, urgent.",
  },
};

export const pct = (n: number, digits = 1) => `${(n * 100).toFixed(digits)}%`;

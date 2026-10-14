import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const TONES = {
  danger: { box: "border-danger/30 bg-danger/[0.06] text-danger", icon: AlertTriangle },
  warning: { box: "border-warning/35 bg-warning/[0.08] text-warning", icon: AlertTriangle },
  success: { box: "border-success/30 bg-success/[0.08] text-success", icon: CheckCircle2 },
} as const;

/** Inline message for a failed or partial action. Announced to screen readers when it appears. */
export function AlertBox({ children, tone = "danger", className }: { children: ReactNode; tone?: keyof typeof TONES; className?: string }) {
  const { box, icon: Icon } = TONES[tone];
  return (
    <div role="alert" className={cn("flex items-start gap-2.5 rounded-xl border px-3.5 py-3 text-sm", box, className)}>
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 text-foreground/90">{children}</div>
    </div>
  );
}

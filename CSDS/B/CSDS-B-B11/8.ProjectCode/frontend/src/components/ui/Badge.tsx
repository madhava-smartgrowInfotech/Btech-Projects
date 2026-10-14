import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type BadgeTone = "neutral" | "violet" | "cyan" | "magenta" | "success" | "warning" | "danger" | "info" | "gradient";

const tones: Record<BadgeTone, string> = {
  neutral: "border-[var(--glass-border)] bg-muted text-muted-foreground",
  violet: "border-violet/30 bg-violet/12 text-violet-ink",
  cyan: "border-cyan/30 bg-cyan/12 text-cyan-ink",
  magenta: "border-magenta/30 bg-magenta/12 text-magenta-ink",
  success: "border-success/30 bg-success/12 text-success",
  warning: "border-warning/35 bg-warning/12 text-warning",
  danger: "border-danger/30 bg-danger/12 text-danger",
  info: "border-info/30 bg-info/12 text-info",
  gradient: "border-transparent bg-grad-primary text-white shadow-[0_2px_10px_-2px_rgba(124,92,255,0.6)]",
};

export function Badge({ tone = "neutral", className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full shrink-0 items-center gap-1 rounded-full border [overflow-wrap:anywhere] px-2 py-0.5 text-[11px] font-medium leading-4 [&_svg]:size-3",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}

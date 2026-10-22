import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

export type MeterTone = "good" | "info" | "warning" | "danger";

export const meterTone = (percentUsed: number): MeterTone => (percentUsed >= 100 ? "danger" : percentUsed >= 90 ? "warning" : percentUsed >= 75 ? "info" : "good");

const FILL: Record<MeterTone, string> = {
  good: "bg-grad-primary",
  info: "bg-[linear-gradient(90deg,var(--info),var(--cyan))]",
  warning: "bg-[linear-gradient(90deg,#fbbf24,#fb923c)]",
  danger: "bg-grad-danger",
};

/** Progress bar whose colour follows a threshold (budget usage) instead of always being violet. */
export function Meter({ value, tone = "good", label, className }: { value: number; tone?: MeterTone; label: string; className?: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-muted", className)}
    >
      <motion.div
        className={cn("absolute inset-y-0 left-0 rounded-full", FILL[tone])}
        initial={false}
        animate={{ width: `${clamped}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
}

import { motion, useReducedMotion } from "framer-motion";

import { probFill } from "@/lib/retina";
import { cn } from "@/lib/utils";

/** Probability bar with an optional decision-threshold marker. Screen readers get the value as text. */
export function ProbBar({ value, threshold, label }: { value: number | null | undefined; threshold?: number; label: string }) {
  const reduce = useReducedMotion();
  const v = Math.round((value ?? 0) * 100);
  return (
    <div className="relative pt-2">
      <div
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={v}
        aria-valuetext={`${v}%`}
        className="relative h-3 w-full overflow-hidden rounded-full bg-muted ring-1 ring-[var(--glass-border)]"
      >
        <motion.div
          className={cn("h-full rounded-full shadow-[0_0_12px_-2px_currentColor]", probFill(value))}
          initial={false}
          animate={{ width: `${v}%` }}
          transition={reduce ? { duration: 0 } : { duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      {threshold != null && (
        <span
          title="Decision threshold"
          className="absolute top-0 h-6 w-0.5 rounded-full bg-foreground"
          style={{ left: `calc(${threshold * 100}% - 1px)` }}
        />
      )}
    </div>
  );
}

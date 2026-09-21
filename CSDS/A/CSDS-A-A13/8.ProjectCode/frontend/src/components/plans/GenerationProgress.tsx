import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const STAGES = [
  { label: "Checking capacity, accessible seats and paper sizes", until: 0.4 },
  { label: "Allocating halls and colour classes (CP-SAT)", until: 1.4 },
  { label: "Laying out seats in every hall, in parallel", until: Infinity },
  { label: "Re-checking every rule independently", until: Infinity },
];

/** Shown while the solver runs. The request is a single call, so stages advance with elapsed time. */
export function GenerationProgress({ candidates }: { candidates: number }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const id = setInterval(() => setElapsed((performance.now() - start) / 1000), 100);
    return () => clearInterval(id);
  }, []);
  const active = STAGES.findIndex((s) => elapsed < s.until);

  return (
    <div className="rounded-xl border border-primary/30 bg-primary/5 p-5" role="status" aria-live="polite">
      <div className="flex items-center justify-between">
        <div className="font-semibold">Seating {candidates.toLocaleString()} candidates...</div>
        <div className="font-mono text-sm tabular text-muted-foreground">{elapsed.toFixed(1)} s</div>
      </div>
      <ol className="mt-4 space-y-2.5">
        {STAGES.map((stage, i) => {
          const done = i < active;
          const running = i === active;
          return (
            <motion.li
              key={stage.label}
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: done || running ? 1 : 0.45, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 text-sm"
            >
              <span
                className={cn(
                  "flex size-5 shrink-0 items-center justify-center rounded-full border",
                  done && "border-success bg-success text-success-foreground",
                  running && "border-primary text-primary",
                )}
              >
                {done ? <Check className="size-3" strokeWidth={3} /> : running ? <Loader2 className="size-3 animate-spin" /> : null}
              </span>
              {stage.label}
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
}

import { animate, motion, useInView, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

function AnimatedNumber({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduce = useReducedMotion();
  const [display, setDisplay] = useState(reduce ? value : 0);

  useEffect(() => {
    if (!inView) return;
    if (reduce) {
      setDisplay(value);
      return;
    }
    const controls = animate(0, value, { duration: 0.9, ease: "easeOut", onUpdate: (v) => setDisplay(v) });
    return () => controls.stop();
  }, [inView, value, reduce]);

  return <span ref={ref}>{display.toLocaleString("en-IN", { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}</span>;
}

export function StatTile({
  label,
  value,
  suffix,
  decimals = 0,
  hint,
  icon,
  className,
}: {
  label: string;
  value: number | null | undefined;
  suffix?: string;
  decimals?: number;
  hint?: ReactNode;
  icon: ReactNode;
  className?: string;
}) {
  return (
    <motion.div whileHover={{ y: -2 }} transition={{ type: "spring", stiffness: 400, damping: 30 }}>
      <Card className={cn("gap-2 p-4", className)}>
        <div className="flex items-center justify-between text-muted-foreground">
          <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
          <span className="[&_svg]:size-4">{icon}</span>
        </div>
        <div className="font-display text-2xl font-bold tabular-nums">
          {value === null || value === undefined ? (
            <span className="text-muted-foreground">-</span>
          ) : (
            <>
              <AnimatedNumber value={value} decimals={decimals} />
              {suffix && <span className="ml-0.5 text-base font-semibold text-muted-foreground">{suffix}</span>}
            </>
          )}
        </div>
        {hint && <div className="text-xs text-muted-foreground">{hint}</div>}
      </Card>
    </motion.div>
  );
}

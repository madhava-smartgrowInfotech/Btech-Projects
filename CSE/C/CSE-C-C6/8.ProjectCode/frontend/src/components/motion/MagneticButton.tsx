import { motion, useMotionValue, useReducedMotion, useSpring } from "framer-motion";
import { useRef, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * Makes its child lean toward the mouse cursor (spring-damped) and settle back on leave.
 * Ignored for touch/pen input and under reduced motion.
 */
export function MagneticButton({
  children,
  strength = 0.28,
  className,
  disabled,
}: {
  children: ReactNode;
  strength?: number;
  className?: string;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = useReducedMotion();
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 260, damping: 18, mass: 0.4 });
  const sy = useSpring(y, { stiffness: 260, damping: 18, mass: 0.4 });
  const off = Boolean(reduce || disabled);

  return (
    <motion.span
      ref={ref}
      className={cn("inline-flex", className)}
      style={off ? undefined : { x: sx, y: sy }}
      onPointerMove={(e) => {
        if (off || e.pointerType !== "mouse" || !ref.current) return;
        const r = ref.current.getBoundingClientRect();
        x.set((e.clientX - (r.left + r.width / 2)) * strength);
        y.set((e.clientY - (r.top + r.height / 2)) * strength);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </motion.span>
  );
}

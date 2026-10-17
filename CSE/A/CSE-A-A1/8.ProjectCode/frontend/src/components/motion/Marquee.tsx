import { useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const KEYFRAMES = "@keyframes alip-marquee { from { transform: translateX(0) } to { transform: translateX(-100%) } }";

/** Infinite horizontal ticker (CSS transform loop, pauses on hover). A static wrapped row under reduced motion. */
export function Marquee({ children, speed = 40, className }: { children: ReactNode; speed?: number; className?: string }) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={cn("flex flex-wrap justify-center gap-3", className)}>{children}</div>;
  return (
    <div
      className={cn(
        "group relative flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_10%,#000_90%,transparent)]",
        className,
      )}
    >
      {[0, 1].map((copy) => (
        <div
          key={copy}
          aria-hidden={copy === 1 ? true : undefined}
          className="flex shrink-0 items-center gap-3 pr-3 group-hover:[animation-play-state:paused]"
          style={{ animation: `alip-marquee ${speed}s linear infinite` }}
        >
          {children}
        </div>
      ))}
      <style>{KEYFRAMES}</style>
    </div>
  );
}

/* SpotlightCard - a radial light that follows the cursor (React Bits component, themed). */
import { useRef, type MouseEvent, type ReactNode } from "react";

import { cn } from "@/lib/utils";

export default function SpotlightCard({
  children,
  className,
  spotlightColor = "color-mix(in oklch, var(--primary) 18%, transparent)",
}: {
  children: ReactNode;
  className?: string;
  spotlightColor?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function onMove(e: MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
    el.style.setProperty("--spotlight-color", spotlightColor);
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      className={cn(
        "relative overflow-hidden rounded-2xl border bg-card p-6",
        "before:pointer-events-none before:absolute before:inset-0 before:opacity-0 before:transition-opacity before:duration-500 hover:before:opacity-100",
        "before:bg-[radial-gradient(circle_at_var(--mouse-x)_var(--mouse-y),var(--spotlight-color),transparent_80%)]",
        className,
      )}
    >
      {children}
    </div>
  );
}

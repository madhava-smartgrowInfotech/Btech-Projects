import { cn } from "@/lib/utils";

/**
 * Slow-moving aurora light behind the whole app. Three blurred colour fields drift on the
 * animate-aurora-* keyframes in index.css; reduced motion stops the drift via the same stylesheet.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: Math.min(1, Math.max(0, intensity)) }}>
      <div className="absolute -left-[15%] -top-[25%] h-[70vmax] w-[70vmax] rounded-full blur-3xl animate-aurora-1" style={{ background: "var(--aurora-1)" }} />
      <div className="absolute -right-[20%] top-[10%] h-[60vmax] w-[60vmax] rounded-full blur-3xl animate-aurora-2" style={{ background: "var(--aurora-2)" }} />
      <div className="absolute bottom-[-25%] left-[20%] h-[65vmax] w-[65vmax] rounded-full blur-3xl animate-aurora-3" style={{ background: "var(--aurora-3)" }} />
    </div>
  );
}

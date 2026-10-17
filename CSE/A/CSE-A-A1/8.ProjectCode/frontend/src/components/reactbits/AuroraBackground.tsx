import { cn } from "@/lib/utils";

/**
 * Three blurred light blobs drifting slowly behind the page (CSS keyframes from index.css; they stop
 * under prefers-reduced-motion). Fixed, non-interactive, never affects layout.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: intensity }}>
      <div className="absolute -left-[10%] -top-[20%] h-[60vmax] w-[60vmax] animate-aurora-1 rounded-full blur-[110px] will-change-transform" style={{ background: "radial-gradient(circle, var(--aurora-1), transparent 65%)" }} />
      <div className="absolute -right-[15%] top-[10%] h-[55vmax] w-[55vmax] animate-aurora-2 rounded-full blur-[110px] will-change-transform" style={{ background: "radial-gradient(circle, var(--aurora-2), transparent 65%)" }} />
      <div className="absolute -bottom-[25%] left-[20%] h-[55vmax] w-[55vmax] animate-aurora-3 rounded-full blur-[110px] will-change-transform" style={{ background: "radial-gradient(circle, var(--aurora-3), transparent 65%)" }} />
    </div>
  );
}

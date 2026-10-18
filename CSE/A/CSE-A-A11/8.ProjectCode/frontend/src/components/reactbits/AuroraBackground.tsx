import { cn } from "@/lib/utils";

/**
 * Three slow-drifting blurred light fields behind the page (violet / cyan / magenta).
 * Pure CSS: the keyframes live in index.css and are switched off by prefers-reduced-motion.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: intensity }}>
      <div className="absolute -left-[10%] -top-[18%] h-[60vmax] w-[60vmax] animate-aurora-1 rounded-full bg-[var(--aurora-1)] blur-[110px] will-change-transform" />
      <div className="absolute -right-[12%] top-[8%] h-[52vmax] w-[52vmax] animate-aurora-2 rounded-full bg-[var(--aurora-2)] blur-[120px] will-change-transform" />
      <div className="absolute -bottom-[22%] left-[18%] h-[56vmax] w-[56vmax] animate-aurora-3 rounded-full bg-[var(--aurora-3)] blur-[120px] will-change-transform" />
      <div className="bg-dots absolute inset-0 opacity-40 [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />
    </div>
  );
}

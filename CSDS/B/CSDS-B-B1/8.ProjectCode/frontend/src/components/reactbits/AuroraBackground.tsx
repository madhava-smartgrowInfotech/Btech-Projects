import { cn } from "@/lib/utils";

/**
 * Slow-moving aurora light behind the glass surfaces. Three radial-gradient blobs drift on CSS
 * keyframes (stopped by the global prefers-reduced-motion rule in index.css). Gradients, not
 * `filter: blur()`, so the layers stay cheap to paint even without a GPU.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  const blob = (color: string) => ({ background: `radial-gradient(closest-side, ${color}, transparent 100%)` });
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: intensity }}>
      <div className="absolute -left-[15%] -top-[25%] h-[70vmax] w-[70vmax] animate-aurora-1 rounded-full will-change-transform" style={blob("var(--aurora-1)")} />
      <div className="absolute -right-[20%] top-[0%] h-[65vmax] w-[65vmax] animate-aurora-2 rounded-full will-change-transform" style={blob("var(--aurora-2)")} />
      <div className="absolute -bottom-[30%] left-[15%] h-[62vmax] w-[62vmax] animate-aurora-3 rounded-full will-change-transform" style={blob("var(--aurora-3)")} />
      <div className="bg-dots absolute inset-0 opacity-[0.35] [mask-image:radial-gradient(ellipse_at_center,#000_30%,transparent_75%)]" />
    </div>
  );
}

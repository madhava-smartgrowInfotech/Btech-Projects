import { cn } from "@/lib/utils";

/**
 * Slow-moving aurora light behind every screen. Three blurred gradient fields drift on CSS
 * keyframes (defined in index.css). `prefers-reduced-motion` stops the drift in the stylesheet.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  const blob = "absolute rounded-full blur-3xl";
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)}
      style={{ opacity: intensity }}
    >
      <div
        className={cn(blob, "animate-aurora-1 -left-[10%] -top-[15%] h-[55vmax] w-[55vmax]")}
        style={{ background: "var(--aurora-1)" }}
      />
      <div
        className={cn(blob, "animate-aurora-2 -right-[12%] top-[10%] h-[50vmax] w-[50vmax]")}
        style={{ background: "var(--aurora-2)" }}
      />
      <div
        className={cn(blob, "animate-aurora-3 bottom-[-20%] left-[20%] h-[48vmax] w-[48vmax]")}
        style={{ background: "var(--aurora-3)" }}
      />
    </div>
  );
}

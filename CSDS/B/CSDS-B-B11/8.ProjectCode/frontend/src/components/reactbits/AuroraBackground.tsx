import { cn } from "@/lib/utils";

/**
 * Slow-moving aurora light behind every page (Aurora Glass). Three blurred gradient blobs drift on
 * the keyframes declared in index.css. Under reduced motion the CSS collapses them to a still frame.
 */
export function AuroraBackground({ intensity = 1, className }: { intensity?: number; className?: string }) {
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: intensity }}>
      <div
        className="absolute -left-[10%] -top-[15%] size-[60vmax] rounded-full blur-3xl animate-aurora-1"
        style={{ background: "radial-gradient(closest-side, var(--aurora-1), transparent)" }}
      />
      <div
        className="absolute -right-[15%] top-[10%] size-[55vmax] rounded-full blur-3xl animate-aurora-2"
        style={{ background: "radial-gradient(closest-side, var(--aurora-2), transparent)" }}
      />
      <div
        className="absolute bottom-[-20%] left-[20%] size-[50vmax] rounded-full blur-3xl animate-aurora-3"
        style={{ background: "radial-gradient(closest-side, var(--aurora-3), transparent)" }}
      />
    </div>
  );
}

import { cn } from "@/lib/utils";

/**
 * Aurora mesh: three large blurred radial gradients drifting on a slow CSS loop (no WebGL).
 * Adapted from the React Bits "Aurora" idea, rewritten in pure CSS. Frozen under reduced motion.
 */
export function AuroraBackground({ className, intensity = 1 }: { className?: string; intensity?: number }) {
  return (
    <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)} style={{ opacity: intensity }}>
      <div
        className="absolute -left-[20%] -top-[25%] h-[75vmax] w-[75vmax] animate-aurora-1 rounded-full blur-[90px] will-change-transform"
        style={{ background: "radial-gradient(circle at center, var(--aurora-1), transparent 62%)" }}
      />
      <div
        className="absolute -right-[25%] top-[5%] h-[70vmax] w-[70vmax] animate-aurora-2 rounded-full blur-[100px] will-change-transform"
        style={{ background: "radial-gradient(circle at center, var(--aurora-2), transparent 60%)" }}
      />
      <div
        className="absolute -bottom-[35%] left-[15%] h-[70vmax] w-[70vmax] animate-aurora-3 rounded-full blur-[110px] will-change-transform"
        style={{ background: "radial-gradient(circle at center, var(--aurora-3), transparent 60%)" }}
      />
      {/* fine grain + vignette keep the glow from banding */}
      <div className="absolute inset-0 bg-dots opacity-[0.35] [mask-image:radial-gradient(ellipse_at_center,#000_20%,transparent_75%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,transparent_40%,var(--background)_100%)] opacity-40" />
    </div>
  );
}

import { cn } from "@/lib/utils";

// Three slow-moving blurred gradients behind the glass surfaces. Colours and keyframes come from
// the kit's tokens in index.css; index.css already disables the animation under reduced motion.
const BLOBS = [
  { color: "var(--aurora-1)", anim: "animate-aurora-1", pos: "-left-[15%] -top-[25%]" },
  { color: "var(--aurora-2)", anim: "animate-aurora-2", pos: "right-[-15%] top-[10%]" },
  { color: "var(--aurora-3)", anim: "animate-aurora-3", pos: "left-[20%] bottom-[-30%]" },
];

export function AuroraBackground({ intensity = 1, className }) {
  return (
    <div
      aria-hidden
      className={cn("pointer-events-none fixed inset-0 -z-10 overflow-hidden", className)}
      style={{ opacity: Math.min(1, Math.max(0, intensity)) }}
    >
      {BLOBS.map((b) => (
        <div
          key={b.anim}
          className={cn("absolute h-[70vmax] w-[70vmax] rounded-full blur-3xl", b.pos, b.anim)}
          style={{ background: `radial-gradient(closest-side, ${b.color}, transparent)` }}
        />
      ))}
    </div>
  );
}

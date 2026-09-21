/* ShinyText - a soft light sweep across text (React Bits component, Tailwind v4 version). */
import { cn } from "@/lib/utils";

export default function ShinyText({ text, className, speed = 5 }: { text: string; className?: string; speed?: number }) {
  return (
    <span
      className={cn("inline-block bg-clip-text text-transparent motion-safe:animate-shine", className)}
      style={{
        backgroundImage:
          "linear-gradient(120deg, color-mix(in oklch, currentColor 55%, transparent) 40%, currentColor 50%, color-mix(in oklch, currentColor 55%, transparent) 60%)",
        backgroundSize: "200% 100%",
        animationDuration: `${speed}s`,
        WebkitBackgroundClip: "text",
      }}
    >
      {text}
    </span>
  );
}

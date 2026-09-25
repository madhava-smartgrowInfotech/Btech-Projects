import type { ReactNode } from "react";
import { cn } from "@/lib/format";

export function GradientText({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "bg-clip-text text-transparent bg-[linear-gradient(90deg,#14532d,#4d7c0f,#a3e635,#4d7c0f,#14532d)] bg-[length:200%_auto] animate-[gradient-shift_6s_linear_infinite]",
        className
      )}
    >
      {children}
    </span>
  );
}

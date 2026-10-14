import { cn } from "@/lib/utils";

/** Initials in a gradient circle. */
export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(" ")
    .filter(Boolean)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <span className={cn("grid size-8 shrink-0 place-items-center rounded-full bg-grad-accent text-xs font-semibold text-white ring-2 ring-[var(--glass-border)]", className)}>
      {initials || "?"}
    </span>
  );
}

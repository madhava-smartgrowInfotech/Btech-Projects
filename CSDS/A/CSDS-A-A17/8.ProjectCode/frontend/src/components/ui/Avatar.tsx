import { cn } from "@/lib/format";

const PALETTE = ["bg-brand-600", "bg-amber-500", "bg-sky-600", "bg-violet-600", "bg-rose-500"];

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  const color = PALETTE[name.charCodeAt(0) % PALETTE.length];
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full text-white font-semibold text-sm shrink-0",
        color,
        className ?? "h-9 w-9"
      )}
    >
      {initials}
    </div>
  );
}

import { cn } from "@/lib/utils";

const CELLS = [
  [5, 5, "a"], [13, 5, "b"], [21, 5, "a"],
  [5, 13, "b"], [13, 13, "a"], [21, 13, "b"],
  [5, 21, "a"], [13, 21, "b"], [21, 21, "c"],
] as const;

/** The SeatWise mark: a seat grid in an alternating pattern - neighbours never share a colour. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={cn("size-8 shrink-0", className)} aria-hidden>
      <rect width="32" height="32" rx="8" className="fill-primary" />
      {CELLS.map(([x, y, kind]) => (
        <rect
          key={`${x}-${y}`}
          x={x}
          y={y}
          width="6"
          height="6"
          rx="1.8"
          fill={kind === "b" ? "#5EEAD4" : "#FFFFFF"}
          fillOpacity={kind === "c" ? 0.45 : 1}
        />
      ))}
    </svg>
  );
}

export function Logo({ className, markClassName }: { className?: string; markClassName?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark className={markClassName} />
      <span className="font-display text-lg font-semibold tracking-tight">
        Seat<span className="text-primary">Wise</span>
      </span>
    </span>
  );
}

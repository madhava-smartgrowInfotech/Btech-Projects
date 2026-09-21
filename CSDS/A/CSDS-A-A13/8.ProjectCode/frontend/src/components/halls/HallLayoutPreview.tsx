import { useMemo } from "react";
import { cn } from "@/lib/utils";

export function seatLabel(row: number, col: number) {
  let letters = "";
  let n = row;
  while (true) {
    letters = String.fromCharCode(65 + (n % 26)) + letters;
    n = Math.floor(n / 26) - 1;
    if (n < 0) break;
  }
  return `${letters}${col + 1}`;
}

/** A small, non-interactive picture of a hall: seats, blocked seats, accessible seats, aisles and an optional highlighted seat. */
export function HallLayoutPreview({
  rows,
  cols,
  blocked,
  accessible,
  aisles,
  highlight,
  className,
}: {
  rows: number;
  cols: number;
  blocked: string[];
  accessible: string[];
  aisles: number[];
  highlight?: string;
  className?: string;
}) {
  const blockedSet = useMemo(() => new Set(blocked), [blocked]);
  const accessibleSet = useMemo(() => new Set(accessible), [accessible]);
  const template = Array.from({ length: cols }, (_, c) => (aisles.includes(c) && c > 0 ? "6px 1fr" : "1fr")).join(" ");

  return (
    <div
      className={cn("w-full", className)}
      aria-label={highlight ? `Seat ${highlight} in a hall of ${rows} rows by ${cols} seats` : `${rows} rows by ${cols} seats`}
      role="img"
    >
      <div className="mx-auto mb-1.5 h-1 w-1/3 rounded-full bg-muted-foreground/30" title="Front of the hall" />
      <div className="grid gap-[3px]" style={{ gridTemplateColumns: template }}>
        {Array.from({ length: rows }, (_, r) =>
          Array.from({ length: cols }, (_, c) => {
            const label = seatLabel(r, c);
            const mine = label === highlight;
            const cell = (
              <span
                key={label}
                className={cn(
                  "relative aspect-square rounded-[3px]",
                  blockedSet.has(label) ? "bg-transparent ring-1 ring-inset ring-border" : "bg-primary/20",
                  accessibleSet.has(label) && !mine && "bg-success/60",
                  mine && "z-10 bg-primary ring-2 ring-primary ring-offset-2 ring-offset-card",
                )}
              >
                {mine && <span className="absolute inset-0 animate-ping rounded-[3px] bg-primary/60 motion-reduce:hidden" />}
              </span>
            );
            return aisles.includes(c) && c > 0 ? [<span key={`a${label}`} />, cell] : cell;
          }),
        )}
      </div>
    </div>
  );
}

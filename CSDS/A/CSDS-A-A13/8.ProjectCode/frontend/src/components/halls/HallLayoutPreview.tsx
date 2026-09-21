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

/** A small, non-interactive picture of a hall: seats, blocked seats, accessible seats and aisles. */
export function HallLayoutPreview({
  rows,
  cols,
  blocked,
  accessible,
  aisles,
  className,
}: {
  rows: number;
  cols: number;
  blocked: string[];
  accessible: string[];
  aisles: number[];
  className?: string;
}) {
  const blockedSet = useMemo(() => new Set(blocked), [blocked]);
  const accessibleSet = useMemo(() => new Set(accessible), [accessible]);
  const template = Array.from({ length: cols }, (_, c) => (aisles.includes(c) && c > 0 ? "6px 1fr" : "1fr")).join(" ");

  return (
    <div className={cn("w-full", className)} aria-label={`${rows} rows by ${cols} seats`} role="img">
      <div className="mb-1.5 h-1 w-1/3 rounded-full bg-muted-foreground/30 mx-auto" title="Front of the hall" />
      <div className="grid gap-[3px]" style={{ gridTemplateColumns: template }}>
        {Array.from({ length: rows }, (_, r) =>
          Array.from({ length: cols }, (_, c) => {
            const label = seatLabel(r, c);
            const cell = (
              <span
                key={label}
                className={cn(
                  "aspect-square rounded-[3px]",
                  blockedSet.has(label) ? "bg-transparent ring-1 ring-inset ring-border" : "bg-primary/25",
                  accessibleSet.has(label) && "bg-success/70",
                )}
              />
            );
            return aisles.includes(c) && c > 0 ? [<span key={`a${label}`} />, cell] : cell;
          }),
        )}
      </div>
    </div>
  );
}

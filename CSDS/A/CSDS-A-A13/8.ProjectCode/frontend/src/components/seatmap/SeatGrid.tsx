import type { CSSProperties, ReactNode } from "react";
import { seatLabel } from "@/components/halls/HallLayoutPreview";
import { cn } from "@/lib/utils";

export interface GridHall {
  rows: number;
  cols: number;
  blocked: string[];
  aisles: number[];
}

/**
 * Lays out a hall: column numbers across the top, row letters down the side, aisles as gaps.
 * Each seat is drawn by `renderSeat`; blocked seats are drawn here.
 */
export function SeatGrid({
  hall,
  seatSize,
  renderSeat,
  className,
}: {
  hall: GridHall;
  seatSize: number;
  renderSeat: (label: string, row: number, col: number) => ReactNode;
  className?: string;
}) {
  const blocked = new Set(hall.blocked);
  const columns = ["1.5rem"];
  for (let c = 0; c < hall.cols; c++) {
    if (c > 0 && hall.aisles.includes(c)) columns.push(`${Math.round(seatSize * 0.35)}px`);
    columns.push(`${seatSize}px`);
  }
  const style = { gridTemplateColumns: columns.join(" "), "--seat": `${seatSize}px` } as CSSProperties;

  const header: ReactNode[] = [<span key="corner" />];
  for (let c = 0; c < hall.cols; c++) {
    if (c > 0 && hall.aisles.includes(c)) header.push(<span key={`ah${c}`} />);
    header.push(
      <span key={`h${c}`} className="text-center text-2xs font-medium text-muted-foreground tabular">
        {c + 1}
      </span>,
    );
  }

  return (
    <div className={cn("inline-block min-w-full", className)}>
      <div className="mb-3 flex items-center gap-3 pl-6">
        <div className="h-1.5 flex-1 rounded-full bg-gradient-to-r from-transparent via-muted-foreground/30 to-transparent" />
        <span className="text-2xs font-semibold uppercase tracking-widest text-muted-foreground">Front of hall</span>
        <div className="h-1.5 flex-1 rounded-full bg-gradient-to-r from-transparent via-muted-foreground/30 to-transparent" />
      </div>
      <div className="grid w-max items-center gap-1.5" style={style} role="grid" aria-label="Seat map">
        {header}
        {Array.from({ length: hall.rows }, (_, r) => {
          const cells: ReactNode[] = [
            <span key={`r${r}`} className="text-center text-2xs font-medium text-muted-foreground" aria-hidden>
              {seatLabel(r, 0).replace(/\d+$/, "")}
            </span>,
          ];
          for (let c = 0; c < hall.cols; c++) {
            const label = seatLabel(r, c);
            if (c > 0 && hall.aisles.includes(c)) cells.push(<span key={`a${label}`} aria-hidden />);
            cells.push(
              blocked.has(label) ? (
                <span
                  key={label}
                  title={`${label} - not in use`}
                  className="flex size-[var(--seat)] items-center justify-center rounded-lg border border-dashed text-2xs text-muted-foreground/60"
                  style={{ backgroundImage: "repeating-linear-gradient(45deg, transparent 0 5px, hsl(var(--border)) 5px 6px)" }}
                >
                  <span className="sr-only">{label} not in use</span>
                </span>
              ) : (
                <div key={label}>{renderSeat(label, r, c)}</div>
              ),
            );
          }
          return cells;
        })}
      </div>
    </div>
  );
}

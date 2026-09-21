import { motion, useReducedMotion } from "motion/react";
import { CheckCircle2, MapPin, Timer } from "lucide-react";

const ROWS = 6;
const COLS = 8;
const AISLE = 4;
const PAPERS = ["var(--paper-1)", "var(--paper-2)", "var(--paper-3)", "var(--paper-4)"];
const CODES = ["ACF-201", "SWE-202", "DAN-203", "HCA-101"];
const EMPTY = new Set(["B3", "D6", "E2", "F7"]);

/**
 * An illustration of how SeatWise lays out a hall: four papers fill the four colour classes of the
 * seat grid, so no seat touches another of the same paper (diagonals included).
 */
export function HeroHall({ solveSeconds }: { solveSeconds?: number }) {
  const reduce = useReducedMotion();
  return (
    <div className="relative">
      <div className="rounded-2xl border bg-card/90 p-4 shadow-lift backdrop-blur sm:p-5">
        <div className="mb-3 flex items-center justify-between text-xs">
          <span className="font-mono font-semibold">MB-101 · Room 101</span>
          <span className="text-muted-foreground">Front of hall</span>
        </div>
        <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${AISLE}, 1fr) 10px repeat(${COLS - AISLE}, 1fr)` }} aria-hidden>
          {Array.from({ length: ROWS }, (_, r) =>
            Array.from({ length: COLS }, (_, c) => {
              const label = `${String.fromCharCode(65 + r)}${c + 1}`;
              const cls = (r % 2) * 2 + (c % 2);
              const empty = EMPTY.has(label);
              const cell = (
                <motion.span
                  key={label}
                  className="flex aspect-square flex-col justify-end rounded-md border-t-[3px] p-0.5 text-[7px] font-medium leading-none text-muted-foreground sm:text-[8px]"
                  style={
                    empty
                      ? { borderTopColor: "transparent", outline: "1px dashed hsl(var(--border))" }
                      : { borderTopColor: PAPERS[cls], backgroundColor: `color-mix(in srgb, ${PAPERS[cls]} 22%, hsl(var(--card)))` }
                  }
                  initial={reduce ? false : { opacity: 0, scale: 0.6 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: reduce ? 0 : 0.5 + cls * 0.35 + (r + c) * 0.015, duration: 0.3 }}
                >
                  {!empty && <span className="hidden sm:inline">{label}</span>}
                </motion.span>
              );
              return c === AISLE ? [<span key={`aisle-${r}`} />, cell] : cell;
            }),
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
          {CODES.map((code, i) => (
            <span key={code} className="inline-flex items-center gap-1.5">
              <span className="size-2 rounded-sm" style={{ background: PAPERS[i] }} />
              {code}
            </span>
          ))}
        </div>
      </div>

      <motion.div
        className="absolute -right-3 -top-4 flex items-center gap-2 rounded-xl border bg-card px-3 py-2 text-xs font-medium shadow-lift sm:-right-6"
        initial={reduce ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: reduce ? 0 : 2.2 }}
      >
        <CheckCircle2 className="size-4 text-success" /> 0 same-paper neighbours
      </motion.div>
      {solveSeconds !== undefined && (
        <motion.div
          className="absolute -left-3 top-1/2 flex items-center gap-2 rounded-xl border bg-card px-3 py-2 text-xs font-medium shadow-lift sm:-left-8"
          initial={reduce ? false : { opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: reduce ? 0 : 2.5 }}
        >
          <Timer className="size-4 text-primary" /> Solved in {solveSeconds.toFixed(1)} s
        </motion.div>
      )}
      <motion.div
        className="absolute -bottom-5 right-6 flex items-center gap-2 rounded-xl bg-primary px-3 py-2 text-xs font-medium text-primary-foreground shadow-lift"
        initial={reduce ? false : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: reduce ? 0 : 2.8 }}
      >
        <MapPin className="size-4" /> Your seat: C4
      </motion.div>
    </div>
  );
}

/** Two small halls side by side: seating in roll order versus SeatWise's colour classes. */
export function ComparisonGrids() {
  const rows = 5;
  const cols = 6;
  const cell = (colour: string, clash: boolean, key: string) => (
    <span
      key={key}
      className="aspect-square rounded-[4px]"
      style={{ backgroundColor: `color-mix(in srgb, ${colour} 70%, hsl(var(--card)))`, outline: clash ? "2px solid hsl(var(--destructive))" : undefined, outlineOffset: -2 }}
    />
  );
  // Roll order: whole rows of one paper, so neighbours share a paper everywhere.
  const rollOrder = Array.from({ length: rows * cols }, (_, i) => {
    const r = Math.floor(i / cols);
    return cell(PAPERS[Math.min(Math.floor(r / 1.3), 3)], true, `r${i}`);
  });
  const seatwise = Array.from({ length: rows * cols }, (_, i) => {
    const r = Math.floor(i / cols);
    const c = i % cols;
    return cell(PAPERS[(r % 2) * 2 + (c % 2)], false, `s${i}`);
  });
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      {[
        { title: "Seated in roll order", note: "Neighbours write the same paper - every outlined seat is a risk.", grid: rollOrder },
        { title: "Seated by SeatWise", note: "Four papers fill four colour classes. No seat touches its own paper.", grid: seatwise },
      ].map((g) => (
        <figure key={g.title} className="rounded-2xl border bg-card p-5">
          <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }} aria-hidden>
            {g.grid}
          </div>
          <figcaption className="mt-4">
            <div className="font-semibold">{g.title}</div>
            <div className="text-sm text-muted-foreground">{g.note}</div>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

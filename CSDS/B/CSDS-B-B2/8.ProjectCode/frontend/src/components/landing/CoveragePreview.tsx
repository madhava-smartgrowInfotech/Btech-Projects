import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { FileWarning, Navigation } from "lucide-react";
import { ZONE_COLOR, type ZoneLabel } from "@/lib/zones";

/** Illustration for the landing page: a scan reveals a hexagon coverage map, a dead zone becomes a complaint
 *  and the nearest strong zone is suggested. It shows how the product behaves; it is not live data. */
const COLS = 8;
const ROWS = 5;
const R = 22;
const W = Math.sqrt(3) * R;
const PAD = 6;
const DEAD_AT = { col: 5, row: 2 };
const STEP_MS = 650;
const END = COLS + 6;

interface Hex { col: number; row: number; x: number; y: number; label: ZoneLabel; dist: number }

const axial = (col: number, row: number) => ({ q: col - (row - (row & 1)) / 2, r: row });
function hexDistance(a: { col: number; row: number }, b: { col: number; row: number }) {
  const p = axial(a.col, a.row), q = axial(b.col, b.row);
  const dq = p.q - q.q, dr = p.r - q.r;
  return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2;
}
const corners = (x: number, y: number, r: number) =>
  Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 180) * (60 * i - 30);
    return `${(x + r * Math.cos(a)).toFixed(1)},${(y + r * Math.sin(a)).toFixed(1)}`;
  }).join(" ");

export function CoveragePreview() {
  const reduce = useReducedMotion();
  const [step, setStep] = useState(reduce ? END - 1 : 0);

  const hexes = useMemo<Hex[]>(() => {
    const out: Hex[] = [];
    for (let row = 0; row < ROWS; row++)
      for (let col = 0; col < COLS; col++) {
        const dist = hexDistance({ col, row }, DEAD_AT);
        const weakPocket = hexDistance({ col, row }, { col: 1, row: 4 }) === 0;
        const label: ZoneLabel = dist <= 1 ? "Dead" : dist === 2 || weakPocket ? "Weak" : "Strong";
        out.push({ col, row, dist, label, x: PAD + W / 2 + W * (col + 0.5 * (row & 1)), y: PAD + R + 1.5 * R * row });
      }
    return out;
  }, []);
  const dead = hexes.find((h) => h.col === DEAD_AT.col && h.row === DEAD_AT.row)!;
  // nearest strong zone, preferring the upper left so the complaint note never covers it
  const target = hexes.filter((h) => h.label === "Strong").sort((a, b) => a.dist - b.dist || a.row - b.row || a.col - b.col)[0]!;

  useEffect(() => {
    if (reduce) return;
    const id = setInterval(() => setStep((s) => (s + 1) % END), STEP_MS);
    return () => clearInterval(id);
  }, [reduce]);

  const scanCol = Math.min(step, COLS);
  const complaint = step >= COLS + 1;
  const suggest = step >= COLS + 2;
  const width = PAD * 2 + W * (COLS + 0.5);
  const height = PAD * 2 + R * 2 + 1.5 * R * (ROWS - 1);
  const scanX = PAD + W * scanCol;

  return (
    <div className="relative rounded-2xl border bg-card/90 p-4 shadow-2xl shadow-primary/10 backdrop-blur sm:p-5" aria-label="Animated preview: a scan reveals strong, weak and dead zones, then a complaint is registered for the dead zone" role="img">
      <div className="mb-3 flex items-center justify-between">
        <p className="font-display text-sm font-semibold">Coverage preview</p>
        <span className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/60" /><span className="relative h-2 w-2 rounded-full bg-primary" /></span>
          {step < COLS ? "Scanning" : "Zone confirmed"}
        </span>
      </div>

      <div className="relative">
        <svg viewBox={`0 0 ${width.toFixed(0)} ${height.toFixed(0)}`} className="w-full" aria-hidden>
          {hexes.map((h) => {
            const shown = h.col < scanCol;
            return (
              <polygon key={`${h.col}-${h.row}`} points={corners(h.x, h.y, R - 1)} strokeWidth={2} stroke="hsl(var(--card))"
                style={{ fill: shown ? ZONE_COLOR[h.label] : "hsl(var(--muted))", fillOpacity: shown ? 0.78 : 1, transition: "fill 0.45s ease, fill-opacity 0.45s ease" }} />
            );
          })}
          {complaint && (
            <polygon points={corners(dead.x, dead.y, R * 2.75)} fill="none" stroke={ZONE_COLOR.Dead} strokeWidth={2} strokeDasharray="5 5" opacity={0.9} />
          )}
          {suggest && (
            <g>
              <line x1={dead.x} y1={dead.y} x2={target.x} y2={target.y} stroke="hsl(var(--primary))" strokeWidth={2.5} strokeDasharray="6 5" strokeLinecap="round" />
              <circle cx={target.x} cy={target.y} r={7} fill={ZONE_COLOR.Strong} stroke="hsl(var(--card))" strokeWidth={2.5} />
            </g>
          )}
          {step < COLS && !reduce && (
            <motion.g initial={false} animate={{ x: scanX }} transition={{ duration: STEP_MS / 1000, ease: "linear" }}>
              <rect x={-1.5} y={0} width={3} height={height} rx={1.5} fill="hsl(var(--primary))" opacity={0.85} />
              <rect x={-26} y={0} width={26} height={height} fill="url(#scan-fade)" />
            </motion.g>
          )}
          <defs>
            <linearGradient id="scan-fade" x1="0" x2="1">
              <stop offset="0" stopColor="hsl(var(--primary))" stopOpacity="0" />
              <stop offset="1" stopColor="hsl(var(--primary))" stopOpacity="0.18" />
            </linearGradient>
          </defs>
        </svg>

        <AnimatePresence>
          {complaint && (
            <motion.div key="complaint" initial={reduce ? false : { opacity: 0, y: 10, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 6 }}
              className="absolute bottom-2 left-2 flex max-w-[78%] items-start gap-2 rounded-lg border bg-popover/95 px-3 py-2 text-xs shadow-lg">
              <FileWarning className="mt-0.5 h-4 w-4 shrink-0 text-zone-dead" aria-hidden />
              <span><span className="font-semibold">Complaint registered</span><span className="block text-muted-foreground">Dead zone persisted - evidence attached, desk notified</span></span>
            </motion.div>
          )}
          {suggest && (
            <motion.div key="suggest" initial={reduce ? false : { opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="absolute right-2 top-2 inline-flex items-center gap-1.5 rounded-full border bg-popover/95 px-2.5 py-1 text-[11px] font-medium shadow">
              <Navigation className="h-3.5 w-3.5 text-zone-strong" aria-hidden /> Stronger signal nearby
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {(["Strong", "Weak", "Dead"] as const).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: ZONE_COLOR[k] }} aria-hidden /> {k}</span>
        ))}
        <span className="ml-auto hidden sm:inline">Hexagons of about 0.1 km²</span>
      </div>
    </div>
  );
}

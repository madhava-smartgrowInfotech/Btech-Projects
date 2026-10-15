import { cn } from "@/lib/utils";
import type { Factor, WordWeight } from "@/lib/types";

interface Row {
  key: string | number;
  label: string;
  sub?: string | number;
  value: number;
  display: string;
}

/**
 * Diverging horizontal bars around a zero baseline (cyan-violet = pushes toward, magenta = pushes away).
 * Every value is also printed as signed text, so colour never carries meaning alone.
 */
export function DivergingBars({ rows, posLabel, negLabel }: { rows: Row[]; posLabel: string; negLabel: string }) {
  const max = Math.max(...rows.map((r) => Math.abs(r.value)), 1e-9);
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2.5 rounded-sm bg-grad-cool" aria-hidden /> {posLabel}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2.5 rounded-sm bg-grad-danger" aria-hidden /> {negLabel}
        </span>
      </div>
      <ul className="space-y-1">
        {rows.map((r) => {
          const w = (Math.abs(r.value) / max) * 50;
          const pos = r.value >= 0;
          return (
            <li
              key={r.key}
              className="grid grid-cols-[minmax(0,7.5rem)_minmax(0,1fr)_4.25rem] items-center gap-2 rounded-lg px-1.5 py-1 text-xs transition-colors hover:bg-muted sm:grid-cols-[minmax(0,10rem)_minmax(0,1fr)_4.5rem]"
              title={`${r.label}${r.sub !== undefined ? ` (${r.sub})` : ""}: ${r.display}`}
            >
              <div className="min-w-0">
                <div className="truncate font-medium">{r.label}</div>
                {r.sub !== undefined && <div className="truncate text-[11px] text-muted-foreground">{r.sub}</div>}
              </div>
              <div className="relative h-4" aria-hidden>
                <div className="absolute inset-y-0 left-1/2 w-px bg-[var(--glass-border)]" />
                <div
                  className={cn("absolute top-0.5 h-3", pos ? "bg-grad-cool rounded-r-md" : "bg-grad-danger rounded-l-md")}
                  style={{ width: `${Math.max(w, 0.8)}%`, left: pos ? "50%" : `${50 - w}%` }}
                />
              </div>
              <div className="text-right font-mono tabular-nums">{r.display}</div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function CategoryWords({ words, category }: { words?: WordWeight[]; category: string }) {
  if (!words?.length) return <p className="text-sm text-muted-foreground">No explanation available for this complaint.</p>;
  return (
    <DivergingBars
      rows={words.map((w, i) => ({ key: i, label: w.word, value: w.weight, display: `${w.weight >= 0 ? "+" : ""}${w.weight.toFixed(3)}` }))}
      posLabel={`supports “${category}”`}
      negLabel="points to another category"
    />
  );
}

const factorRows = (factors: Factor[], fmt: (n: number) => string): Row[] =>
  factors.map((f) => ({ key: f.factor, label: f.factor, sub: f.value, value: f.impact, display: fmt(f.impact) }));

export function PriorityFactors({ data }: { data?: { target: string; factors: Factor[] } }) {
  if (!data?.factors?.length) return <p className="text-sm text-muted-foreground">No explanation available for this complaint.</p>;
  return (
    <DivergingBars
      rows={factorRows(data.factors, (n) => `${n >= 0 ? "+" : ""}${n.toFixed(2)}`)}
      posLabel={`pushes toward ${data.target}`}
      negLabel={`pushes away from ${data.target}`}
    />
  );
}

export function TimeFactors({ data }: { data?: { baseline_days: number; factors: Factor[] } }) {
  if (!data?.factors?.length) return <p className="text-sm text-muted-foreground">No explanation available for this complaint.</p>;
  return (
    <div>
      <p className="mb-3 text-xs text-muted-foreground">
        Typical request: <b className="text-foreground">{data.baseline_days} days</b>. Each factor adds or removes days from that baseline.
      </p>
      <DivergingBars rows={factorRows(data.factors, (n) => `${n >= 0 ? "+" : ""}${n.toFixed(1)} d`)} posLabel="adds time" negLabel="saves time" />
    </div>
  );
}

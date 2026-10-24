import { useEffect, useState } from "react";
import { Area, AreaChart, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { ChartGradients } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { useReducedMotion } from "framer-motion";

/**
 * Hero card. It replays the README's "Prolonged eye closure" simulation scenario with the same numbers
 * core.simulate() uses: EAR 0.30 for the first 3 s, then 0.10. Labelled as scripted so nothing here
 * pretends to be a camera reading.
 */
const THRESHOLD = 0.21;
const CLOSURE_S = 1.5;
const PERSIST_S = 1.0;
const LENGTH = 9; // seconds shown
const STEP = 0.1;

function earAt(t: number) {
  return t > 3 ? 0.1 : 0.3;
}

export function ScriptedPreview() {
  const reduce = useReducedMotion();
  const [t, setT] = useState(reduce ? LENGTH : 0);

  useEffect(() => {
    if (reduce) return;
    const timer = setInterval(() => setT((v) => (v >= LENGTH + 1.5 ? 0 : v + STEP)), 100);
    return () => clearInterval(timer);
  }, [reduce]);

  const shown = Math.min(t, LENGTH);
  const data = Array.from({ length: Math.floor(shown / STEP) + 1 }, (_, i) => ({ t: +(i * STEP).toFixed(1), ear: earAt(i * STEP) }));
  const closedFor = shown > 3 ? shown - 3 : 0;
  const warning = closedFor >= CLOSURE_S + PERSIST_S;
  const pending = !warning && closedFor >= CLOSURE_S;

  return (
    <div className="glass-strong relative overflow-hidden rounded-3xl p-5" aria-label="Scripted simulation preview">
      <div aria-hidden className="absolute -right-10 -top-10 size-40 rounded-full bg-cyan/25 blur-3xl" />
      <div className="relative mb-3 flex items-center justify-between gap-2">
        <Badge tone="magenta">SIMULATION · scripted</Badge>
        <span className="text-xs tabular-nums text-muted-foreground">{shown.toFixed(1)} s</span>
      </div>
      <div className="relative h-40" role="img" aria-label="Eye aspect ratio dropping below the closed-eye threshold at 3 seconds">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 6, right: 4, bottom: 0, left: -26 }}>
            <ChartGradients id="hero" />
            <XAxis dataKey="t" type="number" domain={[0, LENGTH]} hide />
            <YAxis domain={[0, 0.4]} ticks={[0, 0.1, 0.2, 0.3, 0.4]} stroke="var(--chart-axis)" fontSize={10} tickLine={false} axisLine={false} />
            <ReferenceLine y={THRESHOLD} stroke="#FB7185" strokeDasharray="5 4" />
            <Area type="stepAfter" dataKey="ear" stroke="#22D3EE" strokeWidth={2.5} fill="url(#area-hero-1)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="relative mt-4 flex items-center justify-between gap-3 rounded-2xl border border-[var(--glass-border)] bg-[var(--glass)] p-3">
        <div className="min-w-0">
          <div className="text-xs text-muted-foreground">Rule engine says</div>
          <div className="font-display text-base font-semibold" aria-live="off">
            {warning ? "Possible impairment or drowsiness" : shown < 2 ? "Unable to assess" : "Normal"}
          </div>
        </div>
        <Badge tone={warning ? "danger" : pending ? "warning" : "success"}>
          {warning ? "Warning: stop somewhere safe" : pending ? "Persistence pending" : "No sustained warning"}
        </Badge>
      </div>
      <p className="relative mt-3 text-xs text-muted-foreground">
        Closure of {CLOSURE_S} s plus {PERSIST_S} s of persistence is needed before a warning. Scenario values come from the project&apos;s own simulation.
      </p>
    </div>
  );
}

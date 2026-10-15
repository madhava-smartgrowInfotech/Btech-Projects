import { BadgeCheck, Gauge, Languages, ListTree, Route, ShieldCheck, Timer } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { usePublicStats } from "@/lib/queries";

const pct = (n: number) => `${n.toFixed(1)}%`;
const pct0 = (n: number) => `${Math.round(n)}%`;

/** Measured quality of the shipped model on held-out data (GET /api/public/stats). Real numbers only. */
export function StatsStrip() {
  const query = usePublicStats();

  if (query.isError || (query.data && !query.data.available)) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Measured accuracy appears here after the first evaluation run (<code>python ml/eval.py</code>).
      </p>
    );
  }

  const s = query.data;
  const stats: { icon: ReactNode; label: string; value: number | null | undefined; format: (n: number) => string }[] = s
    ? [
        { icon: <ListTree />, label: "Category correct", value: s.category && s.category.accuracy * 100, format: pct },
        { icon: <Route />, label: "Department correct (top 1)", value: s.department && s.department.accuracy * 100, format: pct },
        { icon: <Route />, label: "Department in top 3", value: s.department?.top3 != null ? s.department.top3 * 100 : null, format: pct },
        { icon: <ShieldCheck />, label: "Priority correct", value: s.priority && s.priority.accuracy * 100, format: pct },
        { icon: <Timer />, label: "Typical time error (days)", value: s.resolution?.median_abs_error_days, format: (n) => n.toFixed(1) },
        { icon: <BadgeCheck />, label: "Learns an officer correction", value: s.agreement_after_feedback != null ? s.agreement_after_feedback * 100 : null, format: pct0 },
        { icon: <Gauge />, label: "Median time with explanations", value: s.latency_ms, format: (n) => `${Math.round(n)} ms` },
      ]
    : [];
  const shown = stats.filter((x) => x.value !== null && x.value !== undefined);

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            How CivicPulse scores on held-out complaints
          </h2>
          {s?.category && (
            <p className="text-sm text-muted-foreground">
              {s.category.n.toLocaleString()} unseen complaints in English, Hindi and Hinglish
              {s.resolution ? ` · ${s.resolution.rows_test.toLocaleString()} real NYC 311 requests for resolution time` : ""} · model v{s.model_version}
            </p>
          )}
        </div>
        {query.isPending ? (
          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-7" role="status" aria-label="Loading results">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-4 lg:grid-cols-7">
            {shown.map((x) => (
              <div key={x.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{x.icon}</span>
                <span className="font-display text-2xl font-semibold sm:text-3xl">
                  <CountUp value={x.value as number} format={x.format} className="text-gradient" />
                </span>
                <span className="text-xs text-muted-foreground">{x.label}</span>
              </div>
            ))}
          </Reveal>
        )}
        {s?.category && (
          <p className="relative mt-6 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-center text-xs text-muted-foreground">
            <Languages className="size-4 text-violet-ink" />
            Category accuracy by language:
            {Object.entries(s.category.by_language).map(([k, v]) => (
              <span key={k}>
                {k} <b className="text-foreground">{(v * 100).toFixed(1)}%</b>
              </span>
            ))}
          </p>
        )}
      </div>
    </section>
  );
}

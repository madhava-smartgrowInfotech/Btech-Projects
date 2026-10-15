import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, Scale, Target } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { evalApi } from "@/lib/api";
import { keys } from "@/lib/queries";

// Shape of GET /api/eval/metrics when an evaluation has been run (see experiments/eval/metrics.json).
interface Metrics {
  available?: boolean;
  generated_at?: string;
  predatory_detection?: { num_examples: number; precision: number; recall: number; f1: number };
}

const pct = (n: number) => `${Math.round(n)}%`;

/** Measured detection quality from the latest evaluation run. Real numbers only - hidden until a run exists. */
export function StatsStrip() {
  const query = useQuery({
    queryKey: keys.evaluation,
    queryFn: async () => (await evalApi.getMetrics()).data as Metrics,
    retry: false,
    staleTime: 10 * 60_000,
  });

  if (query.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Measured results are unavailable right now. The full evaluation is on the Evaluation page.
      </p>
    );
  }

  const d = query.data?.predatory_detection;
  if (query.data && !query.data.available) return null;

  const stats: { icon: ReactNode; label: string; value: number; format: (n: number) => string }[] = d
    ? [
        { icon: <Target />, label: "Precision", value: d.precision * 100, format: pct },
        { icon: <Scale />, label: "Recall", value: d.recall * 100, format: pct },
        { icon: <BadgeCheck />, label: "F1 score", value: d.f1 * 100, format: pct },
      ]
    : [];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            How ClauseGuard scores on predatory clauses
          </h2>
          {d && (
            <p className="text-sm text-muted-foreground">
              Tested on {d.num_examples} curated Indian-law clause examples
              {query.data?.generated_at ? ` · run ${query.data.generated_at.slice(0, 10)}` : ""}
            </p>
          )}
        </div>
        {query.isPending ? (
          <div className="relative grid grid-cols-3 gap-4" role="status" aria-label="Loading results">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-20" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-3 gap-x-4 gap-y-6">
            {stats.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
                <span className="font-display text-2xl font-semibold sm:text-3xl">
                  <CountUp value={s.value} format={s.format} className="text-gradient" />
                </span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </div>
            ))}
          </Reveal>
        )}
      </div>
    </section>
  );
}

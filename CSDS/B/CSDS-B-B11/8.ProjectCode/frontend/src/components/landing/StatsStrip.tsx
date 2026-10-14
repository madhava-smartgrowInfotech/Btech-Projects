import { useQuery } from "@tanstack/react-query";
import { Ban, BadgeCheck, Gauge, ShieldCheck, Target, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { evaluationQuery } from "@/lib/evaluation";

const pct = (n: number) => `${n.toFixed(n >= 10 ? 0 : 1)}%`;

/** Measured results from the latest evaluation run. Every number comes from experiments/eval/metrics.json. */
export function StatsStrip() {
  const query = useQuery(evaluationQuery);

  if (query.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Measured results appear here once the evaluation has been run (see docs/03_HOW_TO_RUN.md).
      </p>
    );
  }

  const data = query.data;
  const stats: { icon: ReactNode; label: string; value: number; format: (n: number) => string }[] = data
    ? [
        {
          icon: <Gauge />,
          label: "Days within ±5 % of the calorie target",
          value: data.meal_plans.days_within_5pct_kcal_pct,
          format: pct,
        },
        {
          icon: <ShieldCheck />,
          label: "Allergen violations in generated plans",
          value: data.meal_plans.safety.allergen_violations,
          format: (n) => Math.round(n).toString(),
        },
        {
          icon: <Target />,
          label: "Right dish in top 1 when matching photos",
          value: data.dish_matching.top1_accuracy_pct,
          format: pct,
        },
        {
          icon: <TrendingUp />,
          label: "Less weight-trend error with adaptation",
          value: data.adaptation.error_reduction_pct,
          format: pct,
        },
        {
          icon: <BadgeCheck />,
          label: "Calorie floor respected",
          value: data.requirements.calorie_floor_respected_pct,
          format: pct,
        },
        {
          icon: <Ban />,
          label: "Unsafe swap suggestions",
          value: data.swaps.unsafe_suggestions,
          format: (n) => Math.round(n).toString(),
        },
      ]
    : [];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            How NutriSense scores on its own test set
          </h2>
          {data && (
            <p className="text-sm text-muted-foreground">
              {data.meal_plans.plans_built} plans for random profiles ({data.meal_plans.days} days), {data.requirements.profiles} calorie profiles and{" "}
              {data.dish_matching.queries} photo-label queries (seed-fixed run).
            </p>
          )}
        </div>

        {query.isPending ? (
          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6" role="status" aria-label="Loading results">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-6">
            {stats.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="grid size-9 place-items-center rounded-xl bg-grad-soft text-violet-ink [&_svg]:size-4">{s.icon}</span>
                <span className="font-display text-2xl font-semibold tabular-nums sm:text-3xl">
                  <CountUp value={s.value} format={s.format} />
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

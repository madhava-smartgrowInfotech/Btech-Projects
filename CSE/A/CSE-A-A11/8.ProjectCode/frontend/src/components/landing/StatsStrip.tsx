import { useQuery } from "@tanstack/react-query";
import { Bot, Boxes, Crosshair, Gauge, Layers, Ruler, Target } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { api } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { PublicStats } from "@/lib/types";

const pct = (n: number) => `${Math.round(n)}%`;

/** Measured numbers from the trained model report (GET /public/stats). Real numbers only. */
export function StatsStrip() {
  const query = useQuery({
    queryKey: keys.stats,
    queryFn: async () => (await api.get<PublicStats>("/public/stats")).data,
    retry: false,
    staleTime: 10 * 60_000,
  });

  if (query.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Model results appear here once the API is running (start it with run.bat).
      </p>
    );
  }

  const s = query.data;
  const stats: { icon: ReactNode; label: string; value: number; format: (n: number) => string }[] = s
    ? [
        { icon: <Bot />, label: "Cooperating agents", value: s.agents, format: (n) => String(Math.round(n)) },
        { icon: <Ruler />, label: "Source-code metrics", value: s.metrics, format: (n) => String(Math.round(n)) },
        { icon: <Boxes />, label: "Models compared", value: s.models, format: (n) => String(Math.round(n)) },
        { icon: <Layers />, label: "Feature selectors", value: s.selectors, format: (n) => String(Math.round(n)) },
        { icon: <Target />, label: `Accuracy (${s.best_model})`, value: s.accuracy * 100, format: pct },
        { icon: <Gauge />, label: `F1 (${s.best_model})`, value: s.f1 * 100, format: pct },
        { icon: <Crosshair />, label: "Vulnerability-type accuracy", value: s.type_accuracy * 100, format: pct },
      ]
    : [];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            Straight from the trained model report
          </h2>
          {s && (
            <p className="text-sm text-muted-foreground">
              {s.functions.toLocaleString("en-GB")} functions ({s.vulnerable} vulnerable) on a generated Python corpus. Scores are this system&apos;s own, not the paper&apos;s.
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
            {stats.map((x) => (
              <div key={x.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{x.icon}</span>
                <span className="font-display text-2xl font-semibold sm:text-3xl">
                  <CountUp value={x.value} format={x.format} className="text-gradient" />
                </span>
                <span className="text-xs text-muted-foreground">{x.label}</span>
              </div>
            ))}
          </Reveal>
        )}
      </div>
    </section>
  );
}

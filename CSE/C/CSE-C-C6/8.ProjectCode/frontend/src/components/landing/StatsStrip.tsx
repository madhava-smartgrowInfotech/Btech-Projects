import { Gauge, Layers, Percent, Sigma, Target } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { useModel } from "@/lib/queries";

/** Measured quality of the loaded model (GET /api/model). Real numbers only. */
export function StatsStrip() {
  const model = useModel();

  if (model.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Model metrics appear here once the backend is running (double-click run.bat).
      </p>
    );
  }

  const s = model.data?.stats;
  const stats: { icon: ReactNode; label: string; value: number; format: (n: number) => string }[] = s
    ? [
        { icon: <Target />, label: "Test accuracy", value: s.accuracy * 100, format: (n) => `${n.toFixed(1)}%` },
        { icon: <Gauge />, label: "Macro F1", value: s.f1_macro, format: (n) => n.toFixed(3) },
        { icon: <Percent />, label: "PCA variance kept", value: s.pca_variance * 100, format: (n) => `${n.toFixed(1)}%` },
        { icon: <Layers />, label: "Components Firefly kept", value: s.n_selected, format: (n) => `${Math.round(n)} of ${s.n_pca}` },
        { icon: <Sigma />, label: "Training documents", value: s.n_docs, format: (n) => Math.round(n).toLocaleString("en-US") },
      ]
    : [];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            The loaded model, by the numbers
          </h2>
          <p className="text-sm text-muted-foreground">
            Scored on a held-out 20% test split of its demo corpus (template-style articles), so treat them as a pipeline check, not a real-world claim.
          </p>
        </div>
        {model.isPending ? (
          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5" role="status" aria-label="Loading metrics">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-5">
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

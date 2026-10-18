import { BrainCircuit, ImageIcon, Layers, Target } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { useConfig, useDataset, useModel } from "@/lib/queries";

/** Real numbers from the API: classes the CNN knows, images collected and the last measured test accuracy. */
export function StatsStrip() {
  const config = useConfig();
  const dataset = useDataset();
  const model = useModel();

  if (config.isError || dataset.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Live numbers appear here when the SignSpeak server is running (use run.bat).
      </p>
    );
  }

  const loading = config.isPending || dataset.isPending || model.isPending;
  const total = config.data?.classes.length ?? 29;
  const withData = dataset.data?.trainable_classes.length ?? 0;
  const stats: { icon: ReactNode; label: string; value: number | null; format: (n: number) => string }[] = [
    { icon: <Layers />, label: "Gesture classes", value: config.data?.classes.length ?? null, format: (n) => String(Math.round(n)) },
    { icon: <ImageIcon />, label: "Images collected", value: dataset.data?.total ?? null, format: (n) => Math.round(n).toLocaleString("en-US") },
    { icon: <BrainCircuit />, label: "Classes with data", value: withData, format: (n) => `${Math.round(n)} / ${total}` },
    {
      icon: <Target />,
      label: "Test accuracy",
      value: model.data?.test_accuracy != null ? model.data.test_accuracy * 100 : null,
      format: (n) => `${n.toFixed(1)}%`,
    },
  ];
  const shown = stats.filter((s) => s.value !== null);

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Live from your install</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            Measured on your own data, not promised
          </h2>
          {!loading && model.data == null && (
            <p className="text-sm text-muted-foreground">No model has been trained yet, so accuracy appears here after your first training run.</p>
          )}
        </div>
        {loading ? (
          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-4" role="status" aria-label="Loading numbers">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-4">
            {shown.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
                <span className="font-display text-2xl font-semibold sm:text-3xl">
                  <CountUp value={s.value as number} format={s.format} className="text-gradient" />
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

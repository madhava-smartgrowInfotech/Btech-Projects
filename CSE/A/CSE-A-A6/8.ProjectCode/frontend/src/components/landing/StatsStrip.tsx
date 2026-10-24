import { Database, Gauge, ListChecks, Scale } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { useConfig, useHealth } from "@/lib/queries";

/** Real numbers from the API: rule defaults and gates from /config, and how many events this install has logged. */
export function StatsStrip() {
  const config = useConfig();
  const health = useHealth();

  if (config.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Live numbers appear here when the Smart Rider server is running (use run.bat).
      </p>
    );
  }

  const stats: { icon: ReactNode; label: string; value: number | null; format: (n: number) => string }[] = [
    { icon: <ListChecks />, label: "Possible outputs", value: config.data ? Object.keys(config.data.states).length : null, format: (n) => String(Math.round(n)) },
    { icon: <Gauge />, label: "Signal quality gates", value: config.data?.quality_gates.length ?? null, format: (n) => String(Math.round(n)) },
    { icon: <Scale />, label: "Default EAR threshold", value: config.data?.defaults.ear_threshold ?? null, format: (n) => n.toFixed(2) },
    { icon: <Database />, label: "Events logged here", value: health.data?.history_events ?? null, format: (n) => Math.round(n).toLocaleString("en-US") },
  ];
  const loading = config.isPending;

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Live from your install</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            Rules you can read, numbers you can check
          </h2>
          <p className="text-sm text-muted-foreground">No accuracy claim is made: no consented dataset ships with the project.</p>
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
            {stats
              .filter((s) => s.value !== null)
              .map((s) => (
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

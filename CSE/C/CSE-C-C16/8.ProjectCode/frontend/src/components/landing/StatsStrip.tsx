import { Bug, Leaf, ShieldAlert, Sprout } from "lucide-react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { useDiseases, useHealth } from "@/lib/queries";

/** Facts counted from the live knowledge base. Nothing here is a claimed accuracy figure. */
export function StatsStrip() {
  const diseases = useDiseases();
  const health = useHealth();

  if (diseases.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Knowledge-base counts appear here once the API is running (start it with run.bat).
      </p>
    );
  }

  const list = diseases.data ?? [];
  const sick = list.filter((d) => !d.healthy);
  const stats = [
    { icon: <Bug />, label: "Classes recognised", value: list.length },
    { icon: <Sprout />, label: "Crops covered", value: new Set(list.map((d) => d.crop)).size },
    { icon: <Leaf />, label: "Disease entries", value: sick.length },
    { icon: <ShieldAlert />, label: "Rated high severity", value: sick.filter((d) => d.severity === "high").length },
  ];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">What it knows</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            A 38-class PlantVillage / PD36-C knowledge base
          </h2>
          {health.data && (
            <p className="text-sm text-muted-foreground">
              {health.data.trained_model
                ? `Diagnoses come from the trained model ${health.data.engine}.`
                : "Diagnoses currently come from a colour/texture heuristic. Drop a trained CNN into agrivision/models/ and it is loaded automatically."}
            </p>
          )}
        </div>
        {diseases.isPending ? (
          <div className="relative grid grid-cols-2 gap-4 lg:grid-cols-4" role="status" aria-label="Loading counts">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 lg:grid-cols-4">
            {stats.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
                <span className="font-display text-3xl font-semibold sm:text-4xl">
                  <CountUp value={s.value} className="text-gradient" />
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

import { Gauge, HeartPulse, ScanEye, Target } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { LANDING_STATS } from "@/lib/landingStats";

interface Tile {
  icon: ReactNode;
  label: string;
  value: number;
  format: (n: number) => string;
  note: string;
}

const pct = (n: number) => `${Math.round(n)}%`;
const decimal = (n: number) => n.toFixed(3);
const { retina, heart, dataset } = LANDING_STATS;

const TILES: Tile[] = [
  { icon: <ScanEye />, label: "Retinopathy ROC-AUC", value: retina.rocAuc, format: decimal, note: `${retina.testCases} held-out retinal cases` },
  { icon: <Target />, label: "Retinopathy sensitivity", value: retina.sensitivity * 100, format: pct, note: "true cases detected" },
  { icon: <HeartPulse />, label: "Heart-risk ROC-AUC", value: heart.rocAuc, format: decimal, note: `${heart.testCases} held-out clinical cases` },
  { icon: <Gauge />, label: "Heart-risk sensitivity", value: heart.sensitivity * 100, format: pct, note: "true cases detected" },
];

/** Measured results, fixed to the last evaluation run (see lib/landingStats.ts). */
export function StatsStrip() {
  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-7 flex flex-col gap-2 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            How the two models score on held-out test data
          </h2>
          <p className="mx-auto max-w-2xl text-sm text-muted-foreground">
            Trained on {dataset.retinaImages} fundus images and {dataset.heartPatients} de-duplicated heart-disease patients. The retinopathy
            model is a small CPU model, so treat its output as a screening signal. Source: {LANDING_STATS.source}.
          </p>
        </div>
        <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-7 lg:grid-cols-4">
          {TILES.map((tile) => (
            <div key={tile.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
              <span className="text-violet-ink [&_svg]:size-4">{tile.icon}</span>
              <span className="font-display text-3xl font-semibold">
                <CountUp value={tile.value} format={tile.format} className="text-gradient" />
              </span>
              <span className="text-xs font-medium">{tile.label}</span>
              <span className="text-[11px] text-muted-foreground">{tile.note}</span>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}

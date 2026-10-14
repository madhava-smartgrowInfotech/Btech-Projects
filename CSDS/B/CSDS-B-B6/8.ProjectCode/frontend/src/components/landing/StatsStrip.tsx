import { BadgeCheck, Fingerprint, Gauge, HeartPulse, Lock, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

import evaluation from "@/data/evaluation.json";
import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";

const pct = (n: number) => `${Math.round(n)}%`;

/** Measured results from experiments/eval/metrics.json (copied into src/data). Real numbers only. */
const consent = evaluation.online.consent_enforcement;
const consentTrials = Object.values(consent).reduce((sum, c) => sum + c.trials, 0);
const consentCorrect = Object.values(consent).reduce((sum, c) => sum + c.correct, 0);
const tamperRates = Object.values(evaluation.ledger_tamper_detection.detection_rate);

const STATS: { icon: ReactNode; label: string; value: number; format: (n: number) => string; hint: string }[] = [
  {
    icon: <Fingerprint />,
    label: "Patient linkage F1",
    value: evaluation.mpi_linkage.at_threshold.f1 * 100,
    format: pct,
    hint: `${evaluation.mpi_linkage.true_persons} people, ${evaluation.mpi_linkage.hospital_records} hospital records`,
  },
  {
    icon: <BadgeCheck />,
    label: "FHIR R4 resources valid",
    value: (evaluation.fhir_validation.valid / evaluation.fhir_validation.resources_validated) * 100,
    format: pct,
    hint: `${evaluation.fhir_validation.valid.toLocaleString("en-IN")} of ${evaluation.fhir_validation.resources_validated.toLocaleString("en-IN")}`,
  },
  {
    icon: <Lock />,
    label: "Consent checks correct",
    value: (consentCorrect / consentTrials) * 100,
    format: pct,
    hint: `${consentCorrect} of ${consentTrials} through the live API`,
  },
  {
    icon: <ShieldCheck />,
    label: "Tampering detected",
    value: Math.min(...tamperRates) * 100,
    format: pct,
    hint: `${evaluation.ledger_tamper_detection.tamper_trials_per_attack} trials per attack, ${evaluation.ledger_tamper_detection.false_alarms_on_intact_chain} false alarms`,
  },
  {
    icon: <HeartPulse />,
    label: "Heart risk ROC-AUC",
    value: evaluation.risk_models_cv5.heart.roc_auc,
    format: (n) => n.toFixed(2),
    hint: "5-fold cross-validation",
  },
  {
    icon: <Gauge />,
    label: "Diabetes risk ROC-AUC",
    value: evaluation.risk_models_cv5.diabetes.roc_auc,
    format: (n) => n.toFixed(2),
    hint: "5-fold cross-validation",
  },
];

/** Measured quality from the last evaluation run. */
export function StatsStrip() {
  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Measured, not promised</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            How UniHealth scores on its own evaluation
          </h2>
          <p className="text-sm text-muted-foreground">Results from experiments/eval on synthetic Synthea records and the UCI heart and diabetes datasets.</p>
        </div>
        <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-6">
          {STATS.map((s) => (
            <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
              <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
              <span className="font-display text-2xl font-semibold sm:text-3xl">
                <CountUp value={s.value} format={s.format} className="text-gradient" />
              </span>
              <span className="text-xs font-medium text-foreground/90">{s.label}</span>
              <span className="text-[11px] leading-tight text-muted-foreground">{s.hint}</span>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}

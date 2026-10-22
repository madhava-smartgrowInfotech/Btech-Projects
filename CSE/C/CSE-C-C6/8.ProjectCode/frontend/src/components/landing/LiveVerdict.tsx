import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Newspaper } from "lucide-react";
import { useMemo, useState } from "react";

import { LogoMark } from "@/components/brand/Logo";
import { VerdictBadge } from "@/components/detect/VerdictBadge";
import { Skeleton } from "@/components/ui/Feedback";
import { Segmented } from "@/components/ui/Toggles";
import { api, errorMessage, LABELS, type Label, type Prediction } from "@/lib/api";
import { useSamples } from "@/lib/queries";
import { pct, VERDICT } from "@/lib/verdict";

const SHORT: Record<Label, string> = { REAL: "Sourced", "PARTIALLY TRUE": "Mixed", FAKE: "Clickbait" };

/** Live exchange with the real model: one demo-corpus article per class, scored by POST /api/predict. */
export function LiveVerdict() {
  const samples = useSamples();
  const [pick, setPick] = useState<Label>("FAKE");
  const sample = useMemo(() => samples.data?.find((s) => s.label === pick), [samples.data, pick]);
  const result = useQuery({
    queryKey: ["demo-predict", sample?.text],
    enabled: Boolean(sample),
    queryFn: async () => (await api.post<Prediction>("/predict", { text: sample!.text })).data,
    staleTime: Infinity,
    retry: false,
  });
  const r = result.data;

  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-4 rounded sm:-inset-8-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-3 rounded-3xl p-4 sm:p-5">
        <div className="flex items-center gap-2 border-b border-[var(--glass-border)] pb-3 text-xs text-muted-foreground">
          <Newspaper className="size-4 text-violet-ink" /> Live demo · scored by the loaded model
          <span className="ml-auto flex gap-1" aria-hidden>
            <span className="size-2 rounded-full bg-magenta/70" />
            <span className="size-2 rounded-full bg-violet/70" />
            <span className="size-2 rounded-full bg-cyan/70" />
          </span>
        </div>
        <Segmented
          label="Demo article"
          size="sm"
          value={pick}
          onChange={setPick}
          options={LABELS.map((l) => ({ value: l, label: SHORT[l] }))}
        />
        {samples.isPending ? (
          <Skeleton className="h-24 w-full rounded-2xl" />
        ) : samples.isError ? (
          <p className="rounded-2xl border border-[var(--glass-border)] p-3 text-sm text-muted-foreground">
            The live demo needs the backend: {errorMessage(samples.error)}
          </p>
        ) : (
          <>
            <motion.div
              key={sample?.text}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="ml-auto w-fit max-w-[92%] rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white shadow-[0_8px_24px_-10px_rgba(124,92,255,0.8)]"
            >
              {sample?.text}
            </motion.div>
            <div className="flex gap-2">
              <LogoMark className="size-7" />
              <div className="min-w-0 flex-1 space-y-3 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm" aria-live="polite">
                {result.isPending ? (
                  <div role="status" aria-label="Scoring" className="space-y-2">
                    <Skeleton className="h-6 w-32 rounded-full" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                ) : result.isError || !r ? (
                  <p className="text-muted-foreground">Couldn&apos;t score this one: {errorMessage(result.error)}</p>
                ) : (
                  <motion.div key={r.label + sample?.text} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <VerdictBadge label={r.label} />
                      <span className="text-xs tabular-nums text-muted-foreground">
                        {r.confidence !== null ? `${pct(r.confidence)} confident · ` : ""}
                        {Math.round(r.latency_ms)} ms
                      </span>
                    </div>
                    {r.probabilities && (
                      <ul className="space-y-1.5">
                        {LABELS.map((l) => (
                          <li key={l} className="grid grid-cols-[6.5rem_1fr_2.75rem] items-center gap-2 text-xs">
                            <span className="truncate text-muted-foreground">{l}</span>
                            <span className="h-1.5 overflow-hidden rounded-full bg-muted">
                              <motion.span
                                className="block h-full rounded-full"
                                style={{ background: VERDICT[l].color }}
                                initial={{ width: 0 }}
                                animate={{ width: `${(r.probabilities?.[l] ?? 0) * 100}%` }}
                                transition={{ duration: 0.7, ease: "easeOut" }}
                              />
                            </span>
                            <span className="text-right tabular-nums">{pct(r.probabilities?.[l] ?? 0, 0)}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </motion.div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

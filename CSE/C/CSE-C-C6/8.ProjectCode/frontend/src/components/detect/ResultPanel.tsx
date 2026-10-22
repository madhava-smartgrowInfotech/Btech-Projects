import { CheckCircle2, Clock, Lightbulb, TriangleAlert } from "lucide-react";

import { ProbabilityChart } from "@/components/detect/ProbabilityChart";
import { VerdictBadge } from "@/components/detect/VerdictBadge";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/Feedback";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import type { Prediction } from "@/lib/api";
import { pct, VERDICT } from "@/lib/verdict";

function CueList({ words, tone, empty }: { words: string[]; tone: "danger" | "success"; empty: string }) {
  if (!words.length) return <p className="text-sm text-muted-foreground">{empty}</p>;
  return (
    <ul className="flex flex-wrap gap-1.5">
      {words.map((w) => (
        <li key={w}>
          <Badge tone={tone} className="text-xs">
            {w}
          </Badge>
        </li>
      ))}
    </ul>
  );
}

/** Verdict, confidence, latency, probabilities and the cue words the model can point to. */
export function ResultPanel({ result }: { result: Prediction }) {
  const v = VERDICT[result.label];
  return (
    <Stagger className="space-y-4" aria-live="polite">
      <StaggerItem>
        <Card strong className="space-y-4 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Verdict</p>
              <VerdictBadge label={result.label} size="lg" />
            </div>
            <Badge tone="neutral" className="text-xs">
              <Clock aria-hidden /> {Math.round(result.latency_ms)} ms · {result.word_count} words
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{v.meaning}</p>
          {result.confidence !== null && (
            <div className="space-y-1.5">
              <div className="flex items-baseline justify-between text-sm">
                <span className="font-medium">Confidence</span>
                <span className="font-display text-lg font-semibold tabular-nums">{pct(result.confidence)}</span>
              </div>
              <ProgressBar value={result.confidence * 100} label={`Confidence ${pct(result.confidence)}`} />
            </div>
          )}
        </Card>
      </StaggerItem>

      {result.probabilities && (
        <StaggerItem>
          <ProbabilityChart probabilities={result.probabilities} />
        </StaggerItem>
      )}

      <StaggerItem className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader title="Sensational cues" description="Words typical of clickbait" icon={<TriangleAlert />} />
          <div className="p-5 pt-4">
            <CueList words={result.cues.sensational} tone="danger" empty="None found in this text." />
          </div>
        </Card>
        <Card>
          <CardHeader title="Credibility cues" description="Words typical of sourced reporting" icon={<CheckCircle2 />} />
          <div className="p-5 pt-4">
            <CueList words={result.cues.credibility} tone="success" empty="None found in this text." />
          </div>
        </Card>
      </StaggerItem>

      <StaggerItem>
        <p className="flex items-start gap-2 rounded-2xl border border-[var(--glass-border)] bg-[var(--glass)] px-4 py-3 text-sm text-muted-foreground">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-violet-ink" aria-hidden />
          PARTIALLY TRUE means the text mixes verified facts with unverified or exaggerated claims. Verify the flagged phrases before sharing.
        </p>
      </StaggerItem>
    </Stagger>
  );
}

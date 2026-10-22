import { Info, Layers, Terminal } from "lucide-react";

import { VerdictBadge } from "@/components/detect/VerdictBadge";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { LABELS } from "@/lib/api";
import { useModel } from "@/lib/queries";
import { pct, VERDICT } from "@/lib/verdict";

const KEYWORDS = ["Fake News Detection", "MSVM", "PCA", "Firefly Algorithm", "Feature Optimisation", "Misinformation Filtering"];

export default function About() {
  const model = useModel();
  return (
    <>
      <PageHeader
        eyebrow="About"
        title="Fake News Detection with an optimised MSVM"
        description="Feature-based, optimised multi-class SVM classification: PCA feature extraction, Firefly feature selection and hyper-parameter tuning, and an explicit PARTIALLY TRUE class."
      />
      <Stagger className="grid gap-6 lg:grid-cols-2">
        <StaggerItem className="lg:col-span-2">
          <Card className="space-y-2 p-5">
            <CardHeader className="px-0 pt-0" icon={<Layers />} title="The pipeline" description="What happens to every article you submit" />
            {model.isPending ? (
              <div className="space-y-3" role="status" aria-label="Loading pipeline">
                {[0, 1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : model.isError ? (
              <ErrorState error={model.error} title="Couldn't load the pipeline" onRetry={() => model.refetch()} />
            ) : (
              <ol className="grid gap-3 pt-2 sm:grid-cols-2 xl:grid-cols-4">
                {model.data.pipeline.map((s, i) => (
                  <li key={s.title} className="glass-flat space-y-2 rounded-2xl p-4">
                    <span className="grid size-8 place-items-center rounded-full bg-grad-primary text-sm font-semibold text-white">{i + 1}</span>
                    <h3 className="font-display font-semibold">{s.title}</h3>
                    <p className="text-sm text-muted-foreground">{s.text}</p>
                  </li>
                ))}
              </ol>
            )}
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="h-full space-y-1 p-5">
            <CardHeader className="px-0 pt-0" icon={<Info />} title="Output classes" />
            <ul className="divide-y divide-[var(--glass-border)]">
              {LABELS.map((l) => (
                <li key={l} className="flex flex-col gap-1.5 py-3 sm:flex-row sm:items-center sm:gap-4">
                  <span className="sm:w-44 sm:shrink-0">
                    <VerdictBadge label={l} />
                  </span>
                  <span className="text-sm text-muted-foreground">{VERDICT[l].meaning}</span>
                </li>
              ))}
            </ul>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="h-full space-y-1 p-5">
            <CardHeader className="px-0 pt-0" title="The loaded model" description="Read live from the API" />
            {model.isPending ? (
              <Skeleton className="mt-3 h-40 w-full" />
            ) : model.isError ? (
              <p className="pt-3 text-sm text-muted-foreground">Unavailable until the backend is running.</p>
            ) : (
              <KeyValueList
                items={[
                  { label: "Training documents", value: model.data.stats.n_docs.toLocaleString("en-US") },
                  { label: "Features", value: `${model.data.stats.n_total_features} → ${model.data.stats.n_pca} (PCA) → ${model.data.stats.n_selected} (Firefly)` },
                  { label: "Kernel", value: "RBF, one-vs-rest, balanced class weights" },
                  { label: "Test accuracy / macro-F1", value: `${pct(model.data.stats.accuracy, 2)} / ${model.data.stats.f1_macro.toFixed(4)}` },
                ]}
              />
            )}
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="h-full space-y-3 p-5">
            <CardHeader className="px-0 pt-0" title="Keywords" />
            <ul className="flex flex-wrap gap-2">
              {KEYWORDS.map((k) => (
                <li key={k}>
                  <Badge tone="violet" className="text-xs">
                    {k}
                  </Badge>
                </li>
              ))}
            </ul>
            <p className="text-sm text-muted-foreground">
              The model reads writing style and vocabulary. It cannot check facts against sources, so treat a verdict as a prompt to verify, not as proof.
            </p>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="h-full space-y-3 p-5">
            <CardHeader className="px-0 pt-0" icon={<Terminal />} title="Run it locally" />
            <p className="text-sm text-muted-foreground">Double-click <code className="rounded bg-muted px-1.5 py-0.5 text-xs">run.bat</code>, or start the two servers yourself:</p>
            <pre className="scrollbar-thin overflow-x-auto rounded-2xl border border-[var(--glass-border)] bg-muted p-4 text-xs leading-relaxed">{`pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --port 8406
cd frontend && npm install && npm run dev   # http://localhost:5406`}</pre>
          </Card>
        </StaggerItem>
      </Stagger>
    </>
  );
}

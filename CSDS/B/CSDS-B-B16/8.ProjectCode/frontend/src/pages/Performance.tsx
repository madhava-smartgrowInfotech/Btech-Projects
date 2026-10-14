import { lazy, Suspense } from "react";
import { isAxiosError } from "axios";
import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";

import { ChartCard } from "@/components/charts/Chart";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { api, errorMessage } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { ConfusionMatrix, ModelMetrics, MetricsResponse } from "@/lib/types";
import { cn } from "@/lib/utils";

const RocChart = lazy(() => import("@/components/app/RocChart"));

function ConfusionGrid({ cm, labels }: { cm: ConfusionMatrix; labels: [string, string] }) {
  const cell = (value: number, correct: boolean, caption: string) => (
    <div
      role="cell"
      aria-label={`${caption}: ${value}`}
      className={cn(
        "grid aspect-[3/2] place-items-center rounded-xl border text-center",
        correct ? "border-success/30 bg-success/12" : "border-danger/30 bg-danger/10",
      )}
    >
      <div>
        <div className="font-display text-2xl font-semibold tabular-nums">{value}</div>
        <div className="text-[11px] text-muted-foreground">{caption}</div>
      </div>
    </div>
  );
  return (
    <div className="max-w-sm space-y-2 text-xs">
      <div className="grid grid-cols-[72px_1fr_1fr] items-center gap-2">
        <span />
        <span className="text-center text-muted-foreground">Predicted {labels[0]}</span>
        <span className="text-center text-muted-foreground">Predicted {labels[1]}</span>
        <span className="text-right text-muted-foreground">True {labels[0]}</span>
        {cell(cm.tn, true, "True negative")}
        {cell(cm.fp, false, "False positive")}
        <span className="text-right text-muted-foreground">True {labels[1]}</span>
        {cell(cm.fn, false, "False negative")}
        {cell(cm.tp, true, "True positive")}
      </div>
    </div>
  );
}

function ModelPanel({ title, m, labels }: { title: string; m: ModelMetrics; labels: [string, string] }) {
  const t = m.test;
  return (
    <Card className="space-y-6 p-5 sm:p-6">
      <div className="space-y-1">
        <h2 className="font-display text-lg font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">
          {m.model} · {m.dataset}
        </p>
        <p className="text-xs text-muted-foreground">
          Held-out test set: {t.n} cases. Split: {Object.entries(m.split).map(([k, v]) => `${k} ${v}`).join(", ")}. Decision threshold {t.threshold}.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <StatCard label="Accuracy" value={t.accuracy * 100} format={(n) => `${n.toFixed(1)}%`} />
        <StatCard label="Sensitivity" value={t.sensitivity * 100} format={(n) => `${n.toFixed(1)}%`} />
        <StatCard label="Specificity" value={t.specificity * 100} format={(n) => `${n.toFixed(1)}%`} />
        <StatCard label="F1 score" value={t.f1 * 100} format={(n) => `${n.toFixed(1)}%`} />
        <StatCard label="ROC-AUC" value={t.roc_auc} format={(n) => n.toFixed(3)} />
      </div>

      <div className="grid items-start gap-6 md:grid-cols-2">
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Confusion matrix</h3>
          <ConfusionGrid cm={t.confusion_matrix} labels={labels} />
        </div>
        <ChartCard title="ROC curve" description={`AUC ${t.roc_auc.toFixed(3)} on the held-out test set. The dashed line is chance.`}>
          <Suspense fallback={<Skeleton className="h-64 w-full" />}>
            <RocChart curve={t.roc_curve} auc={t.roc_auc} />
          </Suspense>
        </ChartCard>
      </div>

      {m.notes && <p className="text-xs text-muted-foreground">{m.notes}</p>}
    </Card>
  );
}

export default function Performance() {
  const query = useQuery({
    queryKey: keys.metrics,
    queryFn: async () => (await api.get<MetricsResponse>("/metrics")).data,
  });
  const m = query.data;
  const noResults = isAxiosError(query.error) && query.error.response?.status === 404;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Model performance"
        description={
          m?.generated_at
            ? `Measured on held-out test data never used for training · evaluated ${new Date(m.generated_at).toLocaleString()}`
            : "Measured on held-out test data never used for training."
        }
      />

      {query.isPending && (
        <div className="space-y-6" role="status" aria-label="Loading model performance">
          <Skeleton className="h-96 w-full rounded-2xl" />
        </div>
      )}

      {query.isError && noResults && (
        <EmptyState
          icon={<BarChart3 />}
          title="No evaluation results yet"
          description={errorMessage(query.error)}
        />
      )}
      {query.isError && !noResults && (
        <ErrorState error={query.error} title="Couldn't load model performance" hint="Check that the RetinaGuard API is running." onRetry={() => query.refetch()} />
      )}

      {m?.retina && <ModelPanel title="Hypertensive retinopathy: LeNet on Haar wavelets" m={m.retina} labels={["normal", "HR"]} />}
      {m?.heart && <ModelPanel title="Heart-disease risk: Random Forest" m={m.heart} labels={["no CAD", "CAD"]} />}
    </div>
  );
}

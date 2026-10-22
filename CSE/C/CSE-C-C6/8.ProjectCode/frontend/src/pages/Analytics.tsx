import { Activity, Gauge, Layers, Target, TrendingUp, Timer } from "lucide-react";
import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, GlowDot, gridProps } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader } from "@/components/ui/Card";
import { KeyValueList, StatCard } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { Table, type Column } from "@/components/ui/Table";
import { LABELS, type ClassReportRow, type ModelStats } from "@/lib/api";
import { useModel } from "@/lib/queries";
import { pct, VERDICT } from "@/lib/verdict";
import { cn } from "@/lib/utils";

function ConfusionMatrix({ matrix }: { matrix: number[][] }) {
  const max = Math.max(1, ...matrix.flat());
  const total = matrix.flat().reduce((a, b) => a + b, 0);
  return (
    <ChartCard
      title="Confusion matrix"
      description="Test split: rows are the true class, columns what the model predicted"
      icon={<Layers />}
      table={{
        columns: ["True \\ Predicted", ...LABELS],
        rows: matrix.map((row, i) => [LABELS[i], ...row]),
      }}
    >
      <div className="overflow-x-auto">
        <div role="table" aria-label="Confusion matrix" className="mx-auto grid min-w-[300px] max-w-lg grid-cols-[auto_repeat(3,minmax(0,1fr))] gap-1.5 text-sm">
          <div role="row" className="contents">
            <div role="columnheader" className="p-1 text-[11px] text-muted-foreground" />
            {LABELS.map((l) => (
              <div key={l} role="columnheader" className="px-1 pb-1 text-center text-[11px] font-medium leading-tight text-muted-foreground">
                Predicted
                <br />
                {l}
              </div>
            ))}
          </div>
          {matrix.map((row, i) => (
            <div key={LABELS[i]} role="row" className="contents">
              <div role="rowheader" className="flex items-center pr-1 text-[11px] font-medium leading-tight text-muted-foreground">
                True {LABELS[i]}
              </div>
              {row.map((v, j) => {
                const diag = i === j;
                const alpha = 0.12 + 0.78 * (v / max);
                return (
                  <div
                    key={j}
                    role="cell"
                    title={`True ${LABELS[i]}, predicted ${LABELS[j]}: ${v}${total ? ` (${pct(v / total)} of test split)` : ""}`}
                    className={cn(
                      "grid aspect-[4/3] place-items-center rounded-xl border border-[var(--glass-border)] font-display text-xl font-semibold tabular-nums",
                      v > max * 0.55 ? "text-white" : "text-foreground",
                    )}
                    style={{ background: `color-mix(in srgb, ${diag ? "var(--violet)" : "var(--danger)"} ${Math.round(alpha * (v ? 100 : 0))}%, transparent)` }}
                  >
                    {v}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        <p className="mt-3 text-center text-xs text-muted-foreground">Violet = correct predictions on the diagonal, red = mistakes.</p>
      </div>
    </ChartCard>
  );
}

function FireflyCurve({ history }: { history: number[] }) {
  const data = history.map((fitness, i) => ({ generation: i + 1, fitness }));
  const lo = Math.min(...history);
  const hi = Math.max(...history);
  const pad = Math.max((hi - lo) * 0.4, 0.002);
  return (
    <ChartCard
      title="Firefly optimisation curve"
      description="Best cross-validated fitness found in each generation (x-axis: generation)"
      icon={<TrendingUp />}
      empty={history.length ? undefined : "This model has no recorded optimisation history."}
      table={{ columns: ["Generation", "Best CV fitness"], rows: data.map((d) => [d.generation, d.fitness.toFixed(4)]) }}
    >
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
            <ChartGradients id="ff" />
            <CartesianGrid {...gridProps} />
            <XAxis dataKey="generation" {...axisProps} />
            <YAxis domain={[Math.max(0, lo - pad), Math.min(1, hi + pad)]} tickFormatter={(v: number) => v.toFixed(3)} {...axisProps} />
            <Tooltip content={<ChartTooltip formatter={(v) => Number(v).toFixed(4)} labelFormatter={(l) => `Generation ${l}`} />} />
            <Area type="monotone" dataKey="fitness" name="Best CV fitness" stroke="#7C5CFF" strokeWidth={2.5} fill="url(#areaff-0)" activeDot={GlowDot("#7C5CFF")} dot={{ r: 3, fill: "#7C5CFF" }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}

interface ReportRow {
  name: string;
  precision: number;
  recall: number;
  f1: number;
  support: number | null;
}

function reportRows(report: ModelStats["report"]): ReportRow[] {
  const rows: ReportRow[] = [];
  for (const name of [...LABELS, "macro avg", "weighted avg"]) {
    const r = report[name] as ClassReportRow | undefined;
    if (r && typeof r === "object") rows.push({ name, precision: r.precision, recall: r.recall, f1: r["f1-score"], support: r.support });
  }
  return rows;
}

const reportColumns: Column<ReportRow>[] = [
  { key: "name", header: "Class", cell: (r) => <span className={cn("font-medium", !(LABELS as readonly string[]).includes(r.name) && "text-muted-foreground")}>{r.name}</span> },
  { key: "precision", header: "Precision", align: "right", cell: (r) => <span className="tabular-nums">{r.precision.toFixed(3)}</span> },
  { key: "recall", header: "Recall", align: "right", cell: (r) => <span className="tabular-nums">{r.recall.toFixed(3)}</span> },
  { key: "f1", header: "F1-score", align: "right", cell: (r) => <span className="tabular-nums">{r.f1.toFixed(3)}</span> },
  { key: "support", header: "Support", align: "right", cell: (r) => <span className="tabular-nums">{r.support ?? "-"}</span> },
];

interface CompareRow {
  model: string;
  accuracy: number;
  f1: number;
  proposed: boolean;
}

function AnalyticsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading model analytics">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 rounded-2xl" />
        ))}
      </div>
      <Skeleton className="h-16 w-full rounded-2xl" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-80 rounded-2xl" />
        <Skeleton className="h-80 rounded-2xl" />
      </div>
    </div>
  );
}

export default function Analytics() {
  const model = useModel();
  const [reportTab, setReportTab] = useState("table");

  return (
    <>
      <PageHeader
        eyebrow="Model analytics"
        title="How well does the model perform?"
        description="Every number below is read from the loaded model: accuracy and F1 on its held-out test split, how the features were reduced, and what Firefly optimisation found."
      />
      {model.isPending ? (
        <AnalyticsSkeleton />
      ) : model.isError ? (
        <ErrorState error={model.error} title="Couldn't load the model analytics" hint="Check that the backend is running and that models/msvm_model.pkl exists." onRetry={() => model.refetch()} />
      ) : (
        (() => {
          const s = model.data.stats;
          const gain = (s.accuracy - s.baseline_accuracy) * 100;
          const compare: CompareRow[] = [
            { model: "Baseline SVM (PCA, no tuning)", accuracy: s.baseline_accuracy, f1: s.baseline_f1, proposed: false },
            { model: "Proposed PCA + Firefly + MSVM", accuracy: s.accuracy, f1: s.f1_macro, proposed: true },
          ];
          const compareColumns: Column<CompareRow>[] = [
            {
              key: "model",
              header: "Model",
              cell: (r) => (
                <span className="inline-flex flex-wrap items-center gap-2 font-medium">
                  {r.model}
                  {r.proposed && <Badge tone="gradient">Proposed</Badge>}
                </span>
              ),
            },
            { key: "accuracy", header: "Accuracy", align: "right", cell: (r) => <span className="tabular-nums">{pct(r.accuracy, 2)}</span> },
            { key: "f1", header: "Macro-F1", align: "right", cell: (r) => <span className="tabular-nums">{r.f1.toFixed(4)}</span> },
          ];
          return (
            <Stagger className="space-y-6">
              <StaggerItem className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Accuracy" value={s.accuracy * 100} format={(n) => `${n.toFixed(2)}%`} icon={<Target />} hint="held-out test split" />
                <StatCard label="Macro F1" value={s.f1_macro} format={(n) => n.toFixed(4)} icon={<Gauge />} accent="cyan" hint="average over 3 classes" />
                <StatCard label="Features" display={`${s.n_total_features} → ${s.n_selected}`} icon={<Layers />} accent="magenta" hint="all features → Firefly-selected" />
                <StatCard label="Train time" value={s.train_time_s} format={(n) => `${n.toFixed(1)}s`} icon={<Timer />} hint="PCA + Firefly + final fit" />
              </StaggerItem>

              <StaggerItem>
                <Card className="space-y-3 p-5">
                  <CardHeader className="px-0 pt-0" icon={<Activity />} title="What the optimisation did" />
                  <KeyValueList
                    columns={2}
                    items={[
                      { label: "PCA components kept", value: `${s.n_pca} (${pct(s.pca_variance)} of variance)` },
                      { label: "Selected by Firefly", value: `${s.n_selected} of ${s.n_pca} components` },
                      { label: "Best C", value: s.best_C.toFixed(3) },
                      { label: "Best γ (gamma)", value: s.best_gamma.toFixed(5) },
                      { label: "Baseline SVM accuracy", value: pct(s.baseline_accuracy, 2) },
                      { label: "Gain from optimisation", value: `${gain >= 0 ? "+" : ""}${gain.toFixed(2)} pp` },
                      { label: "Training documents", value: s.n_docs.toLocaleString("en-US") },
                      { label: "TF-IDF + stylometric features", value: `${s.n_tfidf} + ${s.n_total_features - s.n_tfidf}` },
                    ]}
                  />
                  <p className="rounded-xl border border-[var(--glass-border)] bg-muted px-3 py-2 text-xs text-muted-foreground">
                    Scores are measured on a 20% test split of the documents this model was trained on. The model shipped with this project was
                    trained on the built-in synthetic demo corpus, so near-perfect scores describe that template-style data, not real-world news. Retrain
                    on your own labelled CSV to get numbers that mean something for your data.
                  </p>
                </Card>
              </StaggerItem>

              <StaggerItem className="grid gap-6 lg:grid-cols-2">
                <ConfusionMatrix matrix={s.confusion_matrix} />
                <FireflyCurve history={s.firefly_history} />
              </StaggerItem>

              <StaggerItem className="grid gap-6 xl:grid-cols-2">
                <Card className="min-w-0 space-y-4 p-5">
                  <CardHeader className="px-0 pt-0" title="Classification report" description="Per-class precision, recall and F1 on the test split" />
                  <Tabs
                    value={reportTab}
                    onValueChange={setReportTab}
                    tabs={[
                      { value: "table", label: "Table" },
                      { value: "raw", label: "Raw text" },
                    ]}
                  >
                    <TabPanel value="table">
                      <Table caption="Classification report" columns={reportColumns} rows={reportRows(s.report)} rowKey={(r) => r.name} pageSize={10} />
                    </TabPanel>
                    <TabPanel value="raw">
                      <pre className="scrollbar-thin overflow-x-auto rounded-2xl border border-[var(--glass-border)] bg-muted p-4 text-xs leading-relaxed">{s.report_str}</pre>
                    </TabPanel>
                  </Tabs>
                </Card>
                <Card className="min-w-0 space-y-4 p-5">
                  <CardHeader className="px-0 pt-0" title="Baseline vs proposed" description="Same test split, same PCA features" />
                  <Table caption="Model comparison" columns={compareColumns} rows={compare} rowKey={(r) => r.model} pageSize={10} />
                  <ul className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    {LABELS.map((l) => (
                      <li key={l} className="inline-flex items-center gap-1.5">
                        <span className="size-2 rounded-full" style={{ background: VERDICT[l].color }} aria-hidden />
                        {l}: {(s.report[l] as ClassReportRow | undefined)?.support ?? "-"} test articles
                      </li>
                    ))}
                  </ul>
                </Card>
              </StaggerItem>
            </Stagger>
          );
        })()
      )}
    </>
  );
}

import { Activity, Dumbbell, FileText, Grid3x3, Layers, LineChart as LineIcon, Target, TrendingDown } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { TrainingCharts } from "@/components/charts/TrainingCharts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { Table, type Column } from "@/components/ui/Table";
import { classLabel, whenTrained } from "@/lib/format";
import { useModel } from "@/lib/queries";
import type { ReportRow } from "@/lib/types";
import { cn } from "@/lib/utils";

function ConfusionMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const rowTotals = matrix.map((r) => r.reduce((a, b) => a + b, 0));
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">Rows are the true class, columns what the model predicted. Brighter cells hold more of that row's test images.</p>
      <div className="scrollbar-thin overflow-auto rounded-xl border border-[var(--glass-border)] p-2">
        <table className="border-separate border-spacing-0.5 text-[10px]" aria-label="Confusion matrix">
          <thead>
            <tr>
              <th className="sticky left-0 bg-popover px-1 text-left font-medium text-muted-foreground">true ↓ / pred →</th>
              {labels.map((l) => (
                <th key={l} scope="col" className="px-1 text-center font-medium text-muted-foreground">
                  {l.length > 3 ? l.slice(0, 3) : l}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={labels[i]}>
                <th scope="row" className="sticky left-0 bg-popover px-1 text-left font-medium text-muted-foreground">
                  {labels[i]}
                </th>
                {row.map((v, j) => {
                  const share = rowTotals[i] ? v / rowTotals[i] : 0;
                  const diag = i === j;
                  return (
                    <td
                      key={j}
                      title={`true ${labels[i]} → predicted ${labels[j]}: ${v}`}
                      className={cn("size-7 min-w-7 rounded text-center tabular-nums", v === 0 && "text-muted-foreground/40")}
                      style={{
                        background:
                          v === 0
                            ? "transparent"
                            : diag
                              ? `rgba(124,92,255,${0.2 + share * 0.75})`
                              : `rgba(244,114,182,${0.25 + Math.min(1, share * 2) * 0.7})`,
                        color: v && share > 0.5 ? "#fff" : undefined,
                      }}
                    >
                      {v || "·"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const f = (v: number) => v.toFixed(2);

export default function Model() {
  const { data, isPending, isError, error, refetch } = useModel();
  const [tab, setTab] = useState("classes");

  if (isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model performance" description="Loading the latest training report…" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" role="status" aria-label="Loading">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }
  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model performance" />
        <ErrorState error={error} title="Couldn't load the model report" hint="Make sure the SignSpeak server is running (run.bat)." onRetry={() => refetch()} />
      </div>
    );
  }
  if (!data) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model performance" description="Test accuracy, per-class scores and the confusion matrix of the trained CNN." />
        <EmptyState
          icon={<Activity />}
          title="No trained model yet"
          description="Once you train the CNN, its measured test accuracy, per-class precision and recall and confusion matrix appear here."
          action={
            <>
              <Button asChild>
                <Link to="/app/train">
                  <Dumbbell /> Train a model
                </Link>
              </Button>
              <Button asChild variant="secondary">
                <Link to="/app/collect">Collect data first</Link>
              </Button>
            </>
          }
        />
      </div>
    );
  }

  const letters = data.report_rows.filter((r) => !["accuracy", "macro avg", "weighted avg"].includes(r.label));
  const summary = data.report_rows.filter((r) => ["macro avg", "weighted avg"].includes(r.label));
  const columns: Column<ReportRow>[] = [
    { key: "label", header: "Class", cell: (r) => <span className="font-medium">{classLabel(r.label)}</span>, sortValue: (r) => r.label },
    { key: "precision", header: "Precision", cell: (r) => f(r.precision), sortValue: (r) => r.precision, align: "right" },
    { key: "recall", header: "Recall", cell: (r) => f(r.recall), sortValue: (r) => r.recall, align: "right" },
    { key: "f1", header: "F1-score", cell: (r) => f(r.f1), sortValue: (r) => r.f1, align: "right" },
    { key: "support", header: "Test images", cell: (r) => r.support, sortValue: (r) => r.support, align: "right" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Evaluation"
        title="Model performance"
        description="Measured on the held-out test split the last training run kept aside."
        actions={
          <Button asChild variant="secondary">
            <Link to="/app/train">
              <Dumbbell /> Train again
            </Link>
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Test accuracy" icon={<Target />} value={data.test_accuracy != null ? data.test_accuracy * 100 : null} format={(n) => `${n.toFixed(1)}%`} display="-" hint="held-out images" />
        <StatCard label="Test loss" icon={<TrendingDown />} accent="magenta" value={data.test_loss} format={(n) => n.toFixed(3)} display="-" hint="lower is better" />
        <StatCard label="Classes" icon={<Layers />} accent="cyan" value={data.labels.length} format={(n) => String(Math.round(n))} display="-" hint="in the trained model" />
        <StatCard
          label="Trained"
          icon={<Activity />}
          display={<span className="text-xl">{whenTrained(data.trained_at)}</span>}
          hint={data.loaded ? <Badge tone="success">Loaded for live use</Badge> : <Badge>Not loaded</Badge>}
        />
      </div>

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "classes", label: "Per class", icon: <Layers /> },
          { value: "confusion", label: "Confusion matrix", icon: <Grid3x3 /> },
          { value: "curves", label: "Training curves", icon: <LineIcon /> },
          { value: "report", label: "Raw report", icon: <FileText /> },
        ]}
      >
        <TabPanel value="classes">
          {letters.length === 0 ? (
            <EmptyState icon={<Layers />} title="No per-class scores found" description="The classification report is empty. Train the model again to regenerate it." />
          ) : (
            <div className="space-y-4">
              <Table columns={columns} rows={letters} rowKey={(r) => r.label} pageSize={10} caption="Precision, recall and F1 per class" />
              {summary.length > 0 && (
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  {summary.map((r) => (
                    <Badge key={r.label} tone="violet">
                      {r.label}: P {f(r.precision)} · R {f(r.recall)} · F1 {f(r.f1)}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}
        </TabPanel>
        <TabPanel value="confusion">
          <Card>
            <CardHeader title="Confusion matrix" icon={<Grid3x3 />} description="Which letters get mixed up." />
            <CardBody>
              {data.confusion_matrix ? (
                <ConfusionMatrix labels={data.confusion_matrix.labels} matrix={data.confusion_matrix.matrix} />
              ) : (
                <EmptyState
                  icon={<Grid3x3 />}
                  title="No confusion matrix saved"
                  description="It is stored when you train from this web app. Train again here to generate it."
                  action={
                    <Button asChild variant="secondary">
                      <Link to="/app/train">Go to Train</Link>
                    </Button>
                  }
                />
              )}
            </CardBody>
          </Card>
        </TabPanel>
        <TabPanel value="curves">
          <TrainingCharts history={data.history} />
        </TabPanel>
        <TabPanel value="report">
          <Card>
            <CardHeader title="classification_report.txt" icon={<FileText />} description="Exactly as saved by the training run." />
            <CardBody>
              <pre className="scrollbar-thin overflow-x-auto rounded-xl border border-[var(--glass-border)] bg-muted p-4 font-mono text-xs leading-relaxed">{data.report || "No report file found."}</pre>
            </CardBody>
          </Card>
        </TabPanel>
      </Tabs>
    </div>
  );
}

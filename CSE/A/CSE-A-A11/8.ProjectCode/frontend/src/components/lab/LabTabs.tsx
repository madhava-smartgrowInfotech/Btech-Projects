import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, FlaskConical, Play } from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { SevBadge } from "@/components/app/Bits";
import { RiskGauge } from "@/components/app/RiskGauge";
import { HBarChart } from "@/components/app/Charts";
import { axisProps, ChartCard, ChartTooltip, gridProps, SERIES } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { ErrorState } from "@/components/ui/Feedback";
import { FormField, Textarea } from "@/components/ui/Field";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/domain";
import type { LabAnalysis, LabReport, MetricInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

const f3 = (n: number) => n.toFixed(3);

/* ------------------------------------------------------------------ 1. pipeline & data */
const STEPS = [
  ["Compute 14 source-code metrics", "per function"],
  ["Run 7 feature-selection methods", "keep the consensus"],
  ["SmoteTomek balancing", "SMOTE oversampling + Tomek-link cleaning"],
  ["Min-Max normalisation", ""],
  ["Train and compare 9 models", ""],
  ["Classify the vulnerability type", ""],
  ["Score functions inside each PR", ""],
];

export function PipelineTab({ R, metrics }: { R: LabReport; metrics: MetricInfo[] }) {
  const cols: Column<MetricInfo>[] = [
    { key: "id", header: "ID", cell: (m) => <Badge tone="violet">{m.id}</Badge> },
    { key: "name", header: "Metric", cell: (m) => m.name },
    { key: "meaning", header: "Meaning", cell: (m) => <span className="text-muted-foreground">{m.meaning}</span>, hideOnCard: false },
  ];
  const balance = [
    { name: "Original train", value: R.train_size },
    { name: "After SmoteTomek", value: R.balanced_train_size },
  ];
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <div className="min-w-0 space-y-5">
        <Card>
          <CardHeader title="Pipeline (paper Fig. 1)" />
          <CardBody>
            <ol className="space-y-2">
              {STEPS.map(([t, d], i) => (
                <li key={t} className="flex items-start gap-3 text-sm">
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-grad-primary text-xs font-semibold text-white">{i + 1}</span>
                  <span><strong>{t}</strong>{d && <span className="text-muted-foreground"> · {d}</span>}</span>
                </li>
              ))}
            </ol>
          </CardBody>
        </Card>
        <section className="space-y-2">
          <h3 className="font-display text-lg font-semibold">The 14 metrics</h3>
          <Table columns={cols} rows={metrics} rowKey={(m) => m.id} pageSize={7} caption="The 14 source-code metrics" />
        </section>
      </div>
      <div className="min-w-0 space-y-5">
        <ChartCard
          title="Training set size"
          description={`Tomek links removed: ${R.tomek_removed}`}
          table={{ columns: ["Set", "Functions"], rows: balance.map((b) => [b.name, b.value]) }}
        >
          <div className="h-60" role="img" aria-label={`Training set grows from ${R.train_size} to ${R.balanced_train_size} after SmoteTomek`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={balance} margin={{ top: 16, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis {...axisProps} width={44} />
                <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip />} />
                <Bar dataKey="value" name="Functions" radius={[8, 8, 0, 0]} fill="#7C5CFF" isAnimationActive={false} label={{ position: "top", fill: "var(--muted-foreground)", fontSize: 11 }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
        <ChartCard
          title="Vulnerable functions by type"
          table={{ columns: ["Type", "Functions"], rows: Object.entries(R.type_counts).map(([k, v]) => [titleCase(k), v]) }}
        >
          <HBarChart data={Object.entries(R.type_counts).map(([k, v]) => ({ name: titleCase(k), value: v }))} color="#FB7185" top={8} valueLabel="Functions" labelWidth={120} />
        </ChartCard>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ 2. feature selection */
export function SelectionTab({ R, metrics }: { R: LabReport; metrics: MetricInfo[] }) {
  const methods = Object.keys(R.fs_scores);
  const label = Object.fromEntries(metrics.map((m) => [m.key, m.label]));
  const features = Object.keys(R.fs_scores[methods[0]] ?? {});
  const norm = useMemo(() => {
    const out: Record<string, Record<string, number>> = {};
    for (const m of methods) {
      const vals = Object.values(R.fs_scores[m]);
      const lo = Math.min(...vals), hi = Math.max(...vals);
      out[m] = Object.fromEntries(Object.entries(R.fs_scores[m]).map(([k, v]) => [k, (v - lo) / (hi - lo || 1)]));
    }
    return out;
  }, [R, methods]);
  const kdata = Object.entries(R.k_scores).map(([k, v]) => ({ k: Number(k), f1: v })).sort((a, b) => a.k - b.k);
  const votes = features
    .map((k) => ({ key: k, metric: label[k] ?? k, votes: R.fs_order.votes[k] ?? 0, rank: R.fs_order.mean_rank[k] ?? 0 }))
    .sort((a, b) => b.votes - a.votes || a.rank - b.rank);
  const vcols: Column<(typeof votes)[number]>[] = [
    { key: "metric", header: "Metric", cell: (v) => v.metric, sortValue: (v) => v.metric },
    { key: "votes", header: "Votes", align: "right", cell: (v) => v.votes, sortValue: (v) => v.votes },
    { key: "rank", header: "Mean rank", align: "right", cell: (v) => v.rank.toFixed(2), sortValue: (v) => v.rank },
  ];
  return (
    <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
      <Card className="min-w-0">
        <CardHeader title="Importance of each metric per selection method" description="Normalised per method: darker is more important" />
        <CardBody className="overflow-x-auto">
          <table className="w-full min-w-[34rem] text-xs">
            <caption className="sr-only">Metric importance by selection method</caption>
            <thead>
              <tr>
                <th scope="col" className="p-1.5 text-left font-medium text-muted-foreground">Metric</th>
                {methods.map((m) => <th key={m} scope="col" className="p-1.5 text-center font-medium text-muted-foreground">{m}</th>)}
              </tr>
            </thead>
            <tbody>
              {features.map((f) => (
                <tr key={f}>
                  <th scope="row" className="whitespace-nowrap p-1.5 text-left font-normal">{label[f] ?? f}</th>
                  {methods.map((m) => (
                    <td key={m} className="p-0.5">
                      <div
                        className="grid h-7 place-items-center rounded-md tabular-nums"
                        style={{ background: `color-mix(in srgb, var(--violet) ${Math.round(norm[m][f] * 85) + 4}%, transparent)`, color: norm[m][f] > 0.55 ? "#fff" : "var(--foreground)" }}
                        title={`${label[f] ?? f} · ${m}: ${R.fs_scores[m][f]}`}
                      >
                        {R.fs_scores[m][f].toFixed(2)}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
      <div className="min-w-0 space-y-5">
        <ChartCard
          title="Validation F1 vs. number of metrics kept"
          table={{ columns: ["k", "F1"], rows: kdata.map((d) => [d.k, f3(d.f1)]) }}
        >
          <div className="h-60" role="img" aria-label={`Validation F1 by number of metrics kept; best k is ${R.best_k}`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={kdata} margin={{ top: 8, right: 12, bottom: 16, left: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="k" {...axisProps} label={{ value: "k (metrics kept)", position: "insideBottom", offset: -8, fill: "var(--muted-foreground)", fontSize: 11 }} />
                <YAxis {...axisProps} width={40} domain={["auto", "auto"]} />
                <Tooltip content={<ChartTooltip formatter={(v) => Number(v).toFixed(3)} labelFormatter={(l) => `k = ${l}`} />} />
                <ReferenceLine x={R.best_k} stroke="#34D399" strokeDasharray="4 4" label={{ value: `best k=${R.best_k}`, fill: "#34D399", fontSize: 11, position: "insideTopRight" }} />
                <Line dataKey="f1" name="F1" stroke="#7C5CFF" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
        <p className="text-sm">
          <strong>Kept {R.best_k} metrics</strong> (paper keeps 5): <span className="text-muted-foreground">{R.selected_labels.slice(0, 6).join(", ")} …</span>
        </p>
        <Table columns={vcols} rows={votes} rowKey={(v) => v.key} pageSize={7} initialSort={{ key: "votes", dir: "desc" }} caption="Votes per metric across selection methods" />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ 3. models */
const MET = [
  ["accuracy", "Accuracy", SERIES[0]],
  ["precision", "Precision", SERIES[1]],
  ["recall", "Recall", SERIES[2]],
  ["f1", "F1", SERIES[3]],
] as const;

export function ModelsTab({ R }: { R: LabReport }) {
  const rows = Object.entries(R.results).map(([model, m]) => ({ model, ...m }));
  const cols: Column<(typeof rows)[number]>[] = [
    { key: "model", header: "Model", cell: (r) => <span className="font-medium">{r.model}{r.model === R.best && <Badge tone="success" className="ml-2">best F1</Badge>}</span>, sortValue: (r) => r.model },
    ...(["accuracy", "precision", "recall", "f1", "auc"] as const).map((k) => ({
      key: k,
      header: k === "f1" ? "F1" : titleCase(k),
      align: "right" as const,
      cell: (r: (typeof rows)[number]) => f3(r[k]),
      sortValue: (r: (typeof rows)[number]) => r[k],
    })),
  ];
  return (
    <div className="space-y-5">
      <ChartCard
        title="Nine models on the held-out test set"
        legend={MET.map(([, l, c]) => ({ label: l, color: c }))}
        table={{ columns: ["Model", "Accuracy", "Precision", "Recall", "F1"], rows: rows.map((r) => [r.model, f3(r.accuracy), f3(r.precision), f3(r.recall), f3(r.f1)]) }}
      >
        <div className="h-80" role="img" aria-label="Grouped bars of accuracy, precision, recall and F1 for each model">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 40, left: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="model" {...axisProps} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis {...axisProps} domain={[0, 1]} width={36} />
              <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => Number(v).toFixed(3)} />} />
              {MET.map(([k, l, c]) => <Bar key={k} dataKey={k} name={l} fill={c} radius={[4, 4, 0, 0]} isAnimationActive={false} />)}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
      <Table columns={cols} rows={rows} rowKey={(r) => r.model} pageSize={9} initialSort={{ key: "f1", dir: "desc" }} caption="Model results" />
      <ChartCard title="Random-forest feature importance" table={{ columns: ["Metric", "Importance"], rows: Object.entries(R.importance).map(([k, v]) => [k, f3(v)]) }}>
        <HBarChart data={Object.entries(R.importance).map(([name, value]) => ({ name, value }))} color="#7C5CFF" top={14} valueLabel="Importance" format={f3} labelWidth={170} />
      </ChartCard>
    </div>
  );
}

/* ------------------------------------------------------------------ 4. ROC & confusion */
const ROC_COLORS = ["#7C5CFF", "#22D3EE", "#F472B6", "#A3E635", "#FBBF24", "#FB923C", "#34D399", "#60A5FA", "#E879F9"];

export function RocTab({ R }: { R: LabReport }) {
  const names = Object.keys(R.roc);
  const [model, setModel] = useState(R.best);
  const cm = R.confusion[model] ?? [[0, 0], [0, 0]];
  const total = cm.flat().reduce((a, b) => a + b, 0) || 1;
  const cell = (v: number, good: boolean) => ({
    background: `color-mix(in srgb, ${good ? "#34D399" : "#FB7185"} ${Math.round((v / total) * 100 * 4) + 8}%, transparent)`,
  });
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <ChartCard
        title="ROC curves"
        description="The best model is drawn thicker. Higher and further left is better."
        legend={names.map((n, i) => ({ label: `${n} (${R.results[n].auc.toFixed(2)})`, color: ROC_COLORS[i % ROC_COLORS.length] }))}
        table={{ columns: ["Model", "AUC"], rows: names.map((n) => [n, R.results[n].auc.toFixed(3)]) }}
        className="min-w-0"
      >
        <div className="h-96" role="img" aria-label="ROC curves for all models">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart margin={{ top: 8, right: 12, bottom: 20, left: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis type="number" dataKey="fpr" domain={[0, 1]} {...axisProps} label={{ value: "False positive rate", position: "insideBottom", offset: -10, fill: "var(--muted-foreground)", fontSize: 11 }} />
              <YAxis type="number" domain={[0, 1]} {...axisProps} width={52} label={{ value: "True positive rate", angle: -90, position: "insideLeft", offset: 4, fill: "var(--muted-foreground)", fontSize: 11 }} />
              <Tooltip content={<ChartTooltip formatter={(v) => Number(v).toFixed(2)} />} />
              <Legend content={() => null} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="var(--muted-foreground)" strokeDasharray="3 5" />
              {names.map((n, i) => (
                <Line
                  key={n}
                  name={n}
                  data={R.roc[n].fpr.map((x, j) => ({ fpr: x, tpr: R.roc[n].tpr[j] }))}
                  dataKey="tpr"
                  stroke={ROC_COLORS[i % ROC_COLORS.length]}
                  strokeWidth={n === R.best ? 3.5 : 1.5}
                  strokeOpacity={n === R.best ? 1 : 0.7}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
      <Card className="min-w-0">
        <CardHeader title="Confusion matrix" description="Counts on the held-out test set" />
        <CardBody className="space-y-4">
          <FormField label="Model">{(p) => <Select {...p} value={model} onValueChange={setModel} options={names.map((n) => ({ value: n, label: n }))} />}</FormField>
          <table className="w-full max-w-md table-fixed text-sm" aria-label={`Confusion matrix for ${model}`}>
            <thead>
              <tr>
                <td />
                <th scope="col" className="p-2 text-center text-xs font-medium text-muted-foreground">Pred safe</th>
                <th scope="col" className="p-2 text-center text-xs font-medium text-muted-foreground">Pred vulnerable</th>
              </tr>
            </thead>
            <tbody>
              {[["Actual safe", 0], ["Actual vulnerable", 1]].map(([lab, r]) => (
                <tr key={lab as string}>
                  <th scope="row" className="p-2 text-left text-xs font-medium text-muted-foreground">{lab}</th>
                  {[0, 1].map((c) => (
                    <td key={c} className="p-1">
                      <div className="grid h-20 place-items-center rounded-xl font-display text-2xl font-semibold tabular-nums" style={cell(cm[r as number][c], r === c)}>
                        {cm[r as number][c]}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ 5. types */
export function TypesTab({ R }: { R: LabReport }) {
  const rows = Object.entries(R.type_report).filter(([k]) => !["macro avg", "weighted avg", "accuracy", "micro avg"].includes(k));
  const data = rows.map(([k, v]) => ({ name: titleCase(k), f1: v["f1-score"], precision: v.precision, recall: v.recall, support: v.support }));
  const cols: Column<(typeof data)[number]>[] = [
    { key: "name", header: "Type", cell: (r) => r.name, sortValue: (r) => r.name },
    { key: "p", header: "Precision", align: "right", cell: (r) => r.precision.toFixed(2), sortValue: (r) => r.precision },
    { key: "r", header: "Recall", align: "right", cell: (r) => r.recall.toFixed(2), sortValue: (r) => r.recall },
    { key: "f", header: "F1", align: "right", cell: (r) => r.f1.toFixed(2), sortValue: (r) => r.f1 },
    { key: "s", header: "Support", align: "right", cell: (r) => r.support, sortValue: (r) => r.support },
  ];
  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[1.2fr_1fr]">
        <ChartCard
          title={`F1 per vulnerability type (overall accuracy ${R.type_accuracy.toFixed(2)})`}
          table={{ columns: ["Type", "F1"], rows: data.map((d) => [d.name, d.f1.toFixed(2)]) }}
          className="min-w-0"
        >
          <div className="h-72" role="img" aria-label="F1 score for each vulnerability type">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 8, right: 8, bottom: 44, left: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} interval={0} angle={-30} textAnchor="end" height={64} />
                <YAxis {...axisProps} domain={[0, 1]} width={32} />
                <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => Number(v).toFixed(2)} />} />
                <Bar dataKey="f1" name="F1" fill="#7C5CFF" radius={[6, 6, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
        <ChartCard title="Metrics that separate vulnerability types" table={{ columns: ["Metric", "Importance"], rows: Object.entries(R.type_importance).map(([k, v]) => [k, f3(v)]) }} className="min-w-0">
          <HBarChart data={Object.entries(R.type_importance).map(([name, value]) => ({ name, value }))} color="#22D3EE" top={8} valueLabel="Importance" format={f3} labelWidth={170} />
        </ChartCard>
      </div>
      <Table columns={cols} rows={data} rowKey={(r) => r.name} pageSize={10} caption="Per-type precision, recall and F1" />
      <p className="text-sm text-muted-foreground">
        Type classification from metrics alone is inherently harder than detection (paper §V). In the PR pipeline the AST/taint rules assign the precise type; this
        classifier is a second opinion for ML-only findings.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ 6. ablation */
export function AblationTab({ R }: { R: LabReport }) {
  const rows = Object.entries(R.ablation).map(([configuration, v]) => ({ configuration, ...v }));
  const cols: Column<(typeof rows)[number]>[] = [
    { key: "c", header: "Configuration", cell: (r) => <span className="font-medium">{r.configuration}</span> },
    { key: "r", header: "Recall", align: "right", cell: (r) => f3(r.recall), sortValue: (r) => r.recall },
    { key: "p", header: "Precision", align: "right", cell: (r) => f3(r.precision), sortValue: (r) => r.precision },
    { key: "f", header: "F1", align: "right", cell: (r) => f3(r.f1), sortValue: (r) => r.f1 },
  ];
  return (
    <div className="space-y-4">
      <Table columns={cols} rows={rows} rowKey={(r) => r.configuration} caption="Ablation" />
      <p className="text-sm text-muted-foreground">
        Honest comparison of the paper&apos;s exact setting (top-5 metrics) against validated feature-count selection and an unbalanced all-metrics baseline on this corpus.
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ 7. try it */
const DEFAULT_CODE = `def get_user(name):
    q = f"SELECT * FROM users WHERE name = '{name}'"
    cur.execute(q)
    return cur.fetchall()
`;

export function TryTab() {
  const [code, setCode] = useState(DEFAULT_CODE);
  const run = useMutation({ mutationFn: async () => (await api.post<LabAnalysis>("/lab/analyze", { code })).data });
  const out = run.data;
  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">Paste a Python function: the app computes its metrics, scores it and runs the static rules.</p>
      <FormField label="Python code">
        {(p) => <Textarea {...p} value={code} onChange={(e) => setCode(e.target.value)} className="min-h-52 font-mono text-xs" spellCheck={false} />}
      </FormField>
      <Button onClick={() => run.mutate()} loading={run.isPending} disabled={!code.trim()}>
        <Play /> Analyse function
      </Button>
      {run.isError && <ErrorState error={run.error} title="Couldn't analyse that code" hint="It must be valid Python source." className="py-8" />}
      {out && (
        <div className="space-y-5">
          {out.functions.map((fn) => (
            <Card key={fn.name}>
              <CardBody className="grid gap-6 md:grid-cols-[14rem_1fr]">
                <RiskGauge score={Math.round(fn.probability * 100)} title={`${fn.name}()`} />
                <div className="min-w-0 space-y-3">
                  <p className="text-sm"><strong>Predicted type:</strong> {fn.vuln_type ? titleCase(fn.vuln_type) : "none"}</p>
                  {fn.drivers.length > 0 && (
                    <ul className="list-disc space-y-1 pl-5 text-sm">
                      {fn.drivers.map((d) => (
                        <li key={d.feature}>{d.feature} = <strong>{d.value}</strong> <span className="text-muted-foreground">(safe avg {d.safe_mean.toFixed(1)})</span></li>
                      ))}
                    </ul>
                  )}
                  <KeyValueList columns={2} items={fn.metrics.map((m) => ({ label: m.label, value: m.value }))} />
                </div>
              </CardBody>
            </Card>
          ))}
          <Card>
            <CardHeader title="Static findings" icon={<FlaskConical />} />
            <CardBody>
              {out.findings.length === 0 ? (
                <p className="flex items-center gap-2 text-sm text-success"><CheckCircle2 className="size-4" /> No static security findings.</p>
              ) : (
                <ul className="space-y-2">
                  {out.findings.map((f, i) => (
                    <li key={i} className={cn("flex items-center gap-3 text-sm")}>
                      <SevBadge severity={f.severity} /> <span>line {f.line}: <strong>{f.title}</strong></span>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}

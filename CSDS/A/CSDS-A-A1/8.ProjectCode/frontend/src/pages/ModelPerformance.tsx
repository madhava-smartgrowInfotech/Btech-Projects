import { useQuery } from "@tanstack/react-query";
import { Activity, BadgeCheck, Ban, Cpu, FileCheck2, Gauge, Quote, Search, Target, Timer } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartTooltip } from "@/components/charts/ChartCard";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/States";
import { StatTile } from "@/components/common/StatTile";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, errorCode } from "@/lib/api";
import { keys } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

type Stats = { n?: number; mean_ms?: number; p50_ms?: number; p95_ms?: number; max_ms?: number };
type RetrievalRow = { n: number; "hit@1": number; "hit@3": number; "hit@5": number; "mrr@10": number; "recall@5"?: number };

interface Metrics {
  run: string;
  updated_at?: string;
  dataset?: Record<string, string | number>;
  settings?: Record<string, string | number>;
  headline?: Record<string, number | null>;
  retrieval?: Record<string, RetrievalRow | Record<string, Stats>>;
  answers?: {
    n: number;
    answer_accuracy: number;
    key_fact_recall: number;
    citation_accuracy: number;
    faithfulness: { mean: number; median: number; bins: { bin: string; count: number }[] };
    abstention: { n: number; accuracy: number; false_abstentions: number };
    latency_ms: Stats;
    stage_latency_ms: Record<string, Stats>;
    by_category?: Record<string, { n: number; accuracy: number }>;
  };
  claims?: { n: number; accuracy: number; labels: string[]; confusion_matrix: number[][] };
  extraction?: { fields: number; accuracy: number; verified_ratio: number; by_field: Record<string, number> };
  models?: { role: string; model: string; purpose: string }[];
}

const METHODS: { key: string; label: string; color: string }[] = [
  { key: "bm25", label: "BM25 (keyword)", color: "var(--series-2)" },
  { key: "dense", label: "Dense (MiniLM)", color: "var(--series-3)" },
  { key: "hybrid", label: "Hybrid (RRF)", color: "var(--series-4)" },
  { key: "hybrid_rerank", label: "Hybrid + re-rank", color: "var(--series-1)" },
];
const METRICS = ["hit@1", "hit@3", "hit@5", "mrr@10"] as const;

const pct = (v: number | null | undefined) => (v === null || v === undefined ? null : Math.round(v * 1000) / 10);

function PlotImage({ run, file }: { run: string; file: string }) {
  return (
    <figure className="overflow-hidden rounded-xl border bg-white">
      <img src={`/api/evaluation/runs/${run}/plots/${file}`} alt={file.replace(/[-_]/g, " ").replace(".png", "")} className="w-full" loading="lazy" />
      <figcaption className="border-t bg-card px-3 py-2 text-xs text-muted-foreground">{file}</figcaption>
    </figure>
  );
}

export default function ModelPerformance() {
  const query = useQuery({
    queryKey: keys.evaluation,
    queryFn: async () => (await api.get<{ run: string; metrics: Metrics; plots: string[] }>("/evaluation/latest")).data,
    retry: false,
  });

  if (query.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-1/3" />
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }
  if (query.isError) {
    if (errorCode(query.error) === "no_evaluation") {
      return (
        <>
          <PageHeader title="Model performance" />
          <EmptyState
            icon={<Activity />}
            title="No evaluation run yet"
            description="Run the evaluation from the project folder with: venv\Scripts\python ml\run_all.py - the results appear here."
          />
        </>
      );
    }
    return <ErrorState error={query.error} onRetry={() => query.refetch()} />;
  }

  const { run, metrics: m, plots } = query.data!;
  const h = m.headline ?? {};
  const retrievalData = METRICS.map((metric) => {
    const row: Record<string, string | number> = { metric: metric.toUpperCase().replace("@", " @") };
    METHODS.forEach(({ key }) => {
      const r = m.retrieval?.[key] as RetrievalRow | undefined;
      if (r) row[key] = pct(r[metric]) ?? 0;
    });
    return row;
  });
  const stages = Object.entries(m.answers?.stage_latency_ms ?? {}).map(([stage, s]) => ({
    stage: stage.replace("_", " "),
    p50: +(((s.p50_ms ?? 0) as number) / 1000).toFixed(2),
    p95: +(((s.p95_ms ?? 0) as number) / 1000).toFixed(2),
  }));
  const fields = Object.entries(m.extraction?.by_field ?? {})
    .map(([field, acc]) => ({ field: field.replace(/_/g, " "), accuracy: pct(acc) ?? 0 }))
    .sort((a, b) => b.accuracy - a.accuracy);
  const cm = m.claims;
  const cmMax = Math.max(1, ...(cm?.confusion_matrix.flat() ?? [1]));

  return (
    <div>
      <PageHeader
        title="Model performance"
        description="How accurately PolicyLens retrieves clauses, answers, cites and extracts - measured on a hand-built evaluation set from the sample policies."
        actions={
          <Badge variant="outline" className="font-mono">
            {run} · {formatDate(m.updated_at, true)}
          </Badge>
        }
      />
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <StatTile label="Retrieval hit@5" value={pct(h.retrieval_hit_at_5)} suffix="%" decimals={1} icon={<Search />} hint="expected clause in top 5" />
          <StatTile label="Answer accuracy" value={pct(h.answer_accuracy)} suffix="%" decimals={1} icon={<Target />} hint="key facts correct" />
          <StatTile label="Citation accuracy" value={pct(h.citation_accuracy)} suffix="%" decimals={1} icon={<Quote />} hint="cites the right clause/page" />
          <StatTile label="Faithfulness" value={h.faithfulness_mean ?? null} suffix="/100" decimals={1} icon={<BadgeCheck />} hint="mean NLI support" />
          <StatTile label="Abstention" value={pct(h.abstention_accuracy)} suffix="%" decimals={0} icon={<Ban />} hint="says “not in policy” correctly" />
          <StatTile label="Median answer" value={h.latency_p50_ms ? h.latency_p50_ms / 1000 : null} suffix="s" decimals={1} icon={<Timer />} hint="end-to-end response" />
          <StatTile label="Card extraction" value={pct(h.extraction_accuracy)} suffix="%" decimals={1} icon={<FileCheck2 />} hint="fields vs. hand-checked values" />
          <StatTile label="Claim verdicts" value={pct(h.claim_verdict_accuracy)} suffix="%" decimals={1} icon={<Gauge />} hint="Claim Copilot accuracy" />
        </div>

        <ChartCard
          title="Retrieval: which method finds the right clause?"
          description={`${(m.retrieval?.hybrid_rerank as RetrievalRow | undefined)?.n ?? "-"} questions with a known supporting clause. Higher is better.`}
          legend={METHODS.map((x) => ({ label: x.label, color: x.color }))}
          table={{
            columns: ["Method", "Hit@1 %", "Hit@3 %", "Hit@5 %", "MRR@10 %", "Recall@5 %"],
            rows: METHODS.map(({ key, label }) => {
              const r = m.retrieval?.[key] as RetrievalRow | undefined;
              return [label, pct(r?.["hit@1"]), pct(r?.["hit@3"]), pct(r?.["hit@5"]), pct(r?.["mrr@10"]), pct(r?.["recall@5"])];
            }),
          }}
          empty={!m.retrieval ? "Retrieval was not evaluated in this run." : undefined}
        >
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={retrievalData} barGap={2} margin={{ left: -16, right: 8, top: 8 }}>
              <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
              <XAxis dataKey="metric" {...axisProps} />
              <YAxis domain={[0, 100]} unit="%" {...axisProps} />
              <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip formatter={(v) => `${v}%`} />} />
              {METHODS.map(({ key, label, color }) => (
                <Bar key={key} dataKey={key} name={label} fill={color} radius={[4, 4, 0, 0]} maxBarSize={22} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Faithfulness of generated answers"
            description={`Mean ${m.answers?.faithfulness.mean ?? "-"} · median ${m.answers?.faithfulness.median ?? "-"} (0-100)`}
            table={{ columns: ["Score band", "Answers"], rows: (m.answers?.faithfulness.bins ?? []).map((b) => [b.bin, b.count]) }}
            empty={!m.answers ? "Answers were not evaluated in this run." : undefined}
          >
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={m.answers?.faithfulness.bins ?? []} margin={{ left: -20, right: 8, top: 16 }}>
                <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                <XAxis dataKey="bin" {...axisProps} />
                <YAxis allowDecimals={false} {...axisProps} />
                <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip labelFormatter={(l) => `Score ${l}`} />} />
                <Bar
                  dataKey="count"
                  name="Answers"
                  fill="var(--series-1)"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={40}
                  label={{ position: "top", fontSize: 11, fill: "var(--muted-foreground)" }}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Response time by stage"
            description="Seconds per question: median and 95th percentile"
            legend={[
              { label: "Median (p50)", color: "var(--series-1)" },
              { label: "p95", color: "var(--series-2)" },
            ]}
            table={{ columns: ["Stage", "p50 s", "p95 s"], rows: stages.map((s) => [s.stage, s.p50, s.p95]) }}
            empty={!stages.length ? "Latency was not recorded in this run." : undefined}
          >
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stages} layout="vertical" barGap={2} margin={{ left: 8, right: 16 }}>
                <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
                <XAxis type="number" unit="s" {...axisProps} />
                <YAxis type="category" dataKey="stage" width={90} {...axisProps} />
                <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip formatter={(v) => `${v} s`} />} />
                <Bar dataKey="p50" name="Median (p50)" fill="var(--series-1)" radius={[0, 4, 4, 0]} maxBarSize={14} />
                <Bar dataKey="p95" name="p95" fill="var(--series-2)" radius={[0, 4, 4, 0]} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Policy Card extraction accuracy by field"
            description={`${m.extraction?.fields ?? "-"} field values compared with hand-checked values · ${pct(m.extraction?.verified_ratio) ?? "-"}% of quotes verified`}
            table={{ columns: ["Field", "Accuracy %"], rows: fields.map((f) => [f.field, f.accuracy]) }}
            empty={!fields.length ? "Extraction was not evaluated in this run." : undefined}
          >
            <ResponsiveContainer width="100%" height={Math.max(200, fields.length * 26 + 20)}>
              <BarChart data={fields} layout="vertical" margin={{ left: 8, right: 36 }}>
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis type="category" dataKey="field" width={140} {...axisProps} />
                <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip formatter={(v) => `${v}%`} />} />
                <Bar
                  dataKey="accuracy"
                  name="Accuracy"
                  fill="var(--series-1)"
                  radius={[0, 4, 4, 0]}
                  maxBarSize={14}
                  label={{ position: "right", fontSize: 11, fill: "var(--muted-foreground)", formatter: (v: unknown) => `${v}%` }}
                />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card className="gap-3">
            <CardHeader>
              <CardTitle className="text-base">Claim Copilot confusion matrix</CardTitle>
              <CardDescription>
                {cm ? `${cm.n} scenarios · accuracy ${pct(cm.accuracy)}% · rows = expected, columns = predicted` : "Claim scenarios were not evaluated in this run."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {cm && (
                <div className="overflow-x-auto">
                  <table className="w-full text-center text-xs">
                    <thead>
                      <tr>
                        <th className="p-1.5" />
                        {cm.labels.map((l) => (
                          <th key={l} className="p-1.5 font-medium text-muted-foreground">
                            {l.replace("_", " ")}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {cm.confusion_matrix.map((row, i) => (
                        <tr key={cm.labels[i]}>
                          <th className="p-1.5 text-right font-medium text-muted-foreground">{cm.labels[i].replace("_", " ")}</th>
                          {row.map((v, j) => (
                            <td key={j} className="p-0.5">
                              <div
                                className="grid h-10 place-items-center rounded-md font-semibold tabular-nums"
                                style={{
                                  background: v ? `color-mix(in oklch, var(--series-1) ${15 + (v / cmMax) * 70}%, transparent)` : "var(--muted)",
                                  color: v / cmMax > 0.55 ? "white" : "var(--foreground)",
                                }}
                                title={`Expected ${cm.labels[i]}, predicted ${cm.labels[j]}: ${v}`}
                              >
                                {v}
                              </div>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="gap-3">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Cpu className="size-4 text-primary" /> Models in this run
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="divide-y text-sm">
                {(m.models ?? []).map((x) => (
                  <li key={x.role} className="flex flex-col gap-0.5 py-2 sm:flex-row sm:items-center sm:justify-between">
                    <span className="font-medium">{x.role}</span>
                    <span className="font-mono text-xs text-muted-foreground">{x.model}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
          <Card className="gap-3">
            <CardHeader>
              <CardTitle className="text-base">Evaluation set</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(m.dataset ?? {}).map(([k, v]) => (
                  <div key={k} className="rounded-lg bg-muted/50 px-3 py-2">
                    <dt className="text-xs capitalize text-muted-foreground">{k.replace(/_/g, " ")}</dt>
                    <dd className="font-medium">{v}</dd>
                  </div>
                ))}
              </dl>
            </CardContent>
          </Card>
        </div>

        {plots.length > 0 && (
          <section>
            <h2 className="mb-3 text-lg font-semibold">Saved plots</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {plots.map((p) => (
                <PlotImage key={p} run={run} file={p} />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

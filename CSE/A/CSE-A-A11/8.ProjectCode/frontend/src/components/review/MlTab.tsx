import { Brain } from "lucide-react";
import { useMemo, useState } from "react";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";

import { ChartTooltip } from "@/components/charts/Chart";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/Feedback";
import { KeyValueList } from "@/components/ui/Display";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { riskColor, titleCase } from "@/lib/domain";
import { useMeta } from "@/lib/hooks";
import type { MlRow, Review } from "@/lib/types";

export function RiskBar({ value }: { value: number }) {
  const color = riskColor(value * 100);
  return (
    <div className="flex items-center gap-2" aria-label={`Risk ${value.toFixed(2)}`}>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full" style={{ width: `${Math.max(2, value * 100)}%`, background: color }} />
      </div>
      <span className="w-9 text-xs tabular-nums">{value.toFixed(2)}</span>
    </div>
  );
}

/** Radar axes are normalised per metric (value / max(value, typical safe value, 1)) exactly like the original chart. */
export function MetricRadar({ metrics, safe, labels }: { metrics: Record<string, number>; safe: Record<string, number>; labels: Record<string, string> }) {
  const data = Object.keys(labels).map((k) => {
    const top = Math.max(metrics[k] ?? 0, safe[k] ?? 0, 1);
    const words = labels[k].split(" ");
    return { axis: `${words[0]} ${words.slice(1, 3).join(" ")}`, "This function": (metrics[k] ?? 0) / top, "Typical safe function": (safe[k] ?? 0) / top };
  });
  return (
    <div className="h-80" role="img" aria-label="Radar chart comparing this function's metrics with a typical safe function">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="70%">
          <PolarGrid stroke="var(--chart-grid)" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} />
          <Radar name="Typical safe function" dataKey="Typical safe function" stroke="#34D399" fill="#34D399" fillOpacity={0.25} isAnimationActive={false} />
          <Radar name="This function" dataKey="This function" stroke="#FB7185" fill="#FB7185" fillOpacity={0.35} isAnimationActive={false} />
          <Tooltip content={<ChartTooltip formatter={(v) => Number(v).toFixed(2)} />} />
        </RadarChart>
      </ResponsiveContainer>
      <ul className="-mt-2 flex justify-center gap-4 text-xs text-muted-foreground" aria-label="Legend">
        <li className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#FB7185]" />This function</li>
        <li className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#34D399]" />Typical safe function</li>
      </ul>
    </div>
  );
}

export function MlTab({ review }: { review: Review }) {
  const meta = useMeta();
  const rows = useMemo(() => [...review.ml].sort((a, b) => b.probability - a.probability), [review.ml]);
  const [pick, setPick] = useState(0);

  if (rows.length === 0)
    return (
      <EmptyState
        icon={<Brain />}
        title="No functions were scored"
        description="The ML agent was disabled in Settings, or the changed code has no parsable Python functions."
      />
    );

  const columns: Column<MlRow>[] = [
    { key: "fn", header: "Function", cell: (r) => <span className="font-mono text-xs">{r.function}</span>, sortValue: (r) => r.function },
    { key: "file", header: "File", cell: (r) => <span className="font-mono text-xs">{r.file}:{r.line}</span>, sortValue: (r) => r.file },
    { key: "risk", header: "Vulnerability risk", cell: (r) => <RiskBar value={r.probability} />, sortValue: (r) => r.probability },
    { key: "type", header: "Predicted type", cell: (r) => (r.vuln_type ? <Badge tone="warning">{titleCase(r.vuln_type)}</Badge> : <span className="text-muted-foreground">-</span>), sortValue: (r) => r.vuln_type ?? "" },
    { key: "drv", header: "Top drivers", cell: (r) => <span className="text-xs text-muted-foreground">{r.drivers.map((d) => d.feature).join(", ") || "-"}</span>, hideOnCard: false },
  ];

  const m = rows[Math.min(pick, rows.length - 1)];
  const labels = Object.fromEntries((meta.data?.metrics ?? []).map((x) => [x.key, x.label]));
  const safe = Object.fromEntries((meta.data?.metrics ?? []).map((x) => [x.key, x.safe_mean]));

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">
        <strong className="text-foreground">Base-paper technique:</strong> each changed function&apos;s source-code metrics (complexity, nesting, argument count, risky
        calls, input sources …) are scored by a model trained to separate vulnerable from safe functions.
      </p>
      <Table columns={columns} rows={rows} rowKey={(r) => `${r.file}:${r.function}:${r.line}`} initialSort={{ key: "risk", dir: "desc" }} caption="ML risk per changed function" pageSize={8} />

      <Card>
        <CardHeader
          title="Inspect a function"
          description="Why the model rates it the way it does"
          action={
            <div className="w-64 max-w-[60vw]">
              <Select
                aria-label="Inspect function"
                value={String(Math.min(pick, rows.length - 1))}
                onValueChange={(v) => setPick(Number(v))}
                options={rows.map((r, i) => ({ value: String(i), label: `${r.function} (${r.file}:${r.line})` }))}
              />
            </div>
          }
        />
        <CardBody className="grid gap-6 lg:grid-cols-2">
          {meta.isPending ? <p className="text-sm text-muted-foreground">Loading metric baselines…</p> : <MetricRadar metrics={m.metrics} safe={safe} labels={labels} />}
          <div className="space-y-4">
            <div className="flex flex-wrap gap-6">
              <div>
                <div className="text-xs text-muted-foreground">Vulnerability probability</div>
                <div className="font-display text-3xl font-semibold tabular-nums">{Math.round(m.probability * 100)}%</div>
              </div>
              {m.vuln_type && (
                <div>
                  <div className="text-xs text-muted-foreground">Most likely type</div>
                  <div className="font-display text-xl font-semibold">{titleCase(m.vuln_type)}</div>
                </div>
              )}
            </div>
            {m.drivers.length > 0 ? (
              <div>
                <div className="mb-1 text-sm font-medium">Why the model is worried</div>
                <ul className="list-disc space-y-1 pl-5 text-sm">
                  {m.drivers.map((d) => (
                    <li key={d.feature}>
                      <strong>{d.feature}</strong> = {d.value} <span className="text-muted-foreground">(typical safe function: {d.safe_mean.toFixed(1)})</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No metric stands out above a typical safe function.</p>
            )}
            <KeyValueList
              columns={1}
              items={Object.keys(labels).map((k) => ({ label: labels[k], value: m.metrics[k] }))}
              className="max-h-64 overflow-auto scrollbar-thin"
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

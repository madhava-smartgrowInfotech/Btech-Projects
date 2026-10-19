import { Gauge, Timer, Zap } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps, SERIES } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useBenchmarks } from "@/lib/queries";
import type { BenchmarkRun } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const f1 = (n: number | null | undefined) => (n === null || n === undefined ? "-" : n.toFixed(1));

function RunCard({ run }: { run: BenchmarkRun }) {
  return (
    <Card>
      <CardHeader
        title={`Run ${run.id}`}
        description={formatDate(run.timestamp, true)}
        icon={<Gauge />}
        action={<Badge tone="neutral">{run.total_ops} voters</Badge>}
      />
      <CardBody className="space-y-4">
        <dl className="grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted-foreground">Sync throughput</dt>
            <dd className="font-display text-xl font-semibold tabular-nums">{f1(run.throughput_sync)} <span className="text-xs font-normal text-muted-foreground">ops/s</span></dd>
            <dd className="text-xs text-muted-foreground">Duration {run.sync_duration?.toFixed(2) ?? "-"} s</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Async throughput</dt>
            <dd className="font-display text-xl font-semibold tabular-nums">{f1(run.throughput_async)} <span className="text-xs font-normal text-muted-foreground">ops/s</span></dd>
            <dd className="text-xs text-muted-foreground">Batch comparison</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Latency</dt>
            <dd className="font-display text-xl font-semibold tabular-nums">{f1(run.mean_latency_ms)} <span className="text-xs font-normal text-muted-foreground">ms mean</span></dd>
            <dd className="text-xs text-muted-foreground">p95 {f1(run.p95_latency_ms)} ms</dd>
          </div>
        </dl>
        {run.details && (
          <details className="group rounded-xl border border-[var(--glass-border)] bg-muted/40">
            <summary className="cursor-pointer select-none rounded-xl px-3 py-2 text-sm font-medium focus-visible:outline-2">Raw details (JSON)</summary>
            <pre className="scrollbar-thin max-h-72 overflow-auto px-3 pb-3 font-mono text-xs">{JSON.stringify(run.details, null, 2)}</pre>
          </details>
        )}
      </CardBody>
    </Card>
  );
}

export default function Benchmarks() {
  const q = useBenchmarks();
  const header = (
    <PageHeader
      eyebrow="Administrator"
      title="Performance benchmarks"
      description="Timings measured from the running implementation with synthetic voters, using Python's perf_counter."
    />
  );

  if (q.isPending) return <>{header}<div className="space-y-4" role="status" aria-label="Loading benchmarks"><Skeleton className="h-72 rounded-2xl" /><Skeleton className="h-48 rounded-2xl" /></div></>;
  if (q.isError) return <>{header}<ErrorState error={q.error} title="Could not load benchmarks" onRetry={() => q.refetch()} /></>;
  if (q.data.length === 0) {
    return (
      <>
        {header}
        <EmptyState
          icon={<Gauge />}
          title="No benchmark runs yet"
          description="Benchmarks come from a command-line run against synthetic voters. Run it, then refresh this page."
          action={<code className="rounded-lg bg-muted px-3 py-2 font-mono text-xs">python -m app.benchmarks.run_benchmark --voters 1000</code>}
        />
      </>
    );
  }

  const latest = q.data[0];
  const batches = Object.entries(latest.details?.async_batches ?? {}).map(([size, s]) => ({
    name: `Batch ${size}`,
    Throughput: Number((s.throughput ?? 0).toFixed(1)),
    Mean: Number((s.mean_ms ?? 0).toFixed(2)),
    P95: Number((s.p95_ms ?? 0).toFixed(2)),
  }));
  const sync = latest.details?.sync;
  const chartRows = sync
    ? [{ name: "Sync", Throughput: Number((sync.throughput ?? 0).toFixed(1)), Mean: Number((sync.mean_ms ?? 0).toFixed(2)), P95: Number((sync.p95_ms ?? 0).toFixed(2)) }, ...batches]
    : batches;

  return (
    <>
      {header}
      <Stagger className="space-y-4">
        <StaggerItem className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Sync throughput" value={latest.throughput_sync ?? 0} format={(n) => `${n.toFixed(1)} ops/s`} icon={<Zap />} hint={`Latest run · ${latest.total_ops} voters`} />
          <StatCard label="Async throughput" value={latest.throughput_async ?? 0} format={(n) => `${n.toFixed(1)} ops/s`} icon={<Zap />} accent="cyan" hint="Batched submission" />
          <StatCard label="Mean latency" value={latest.mean_latency_ms ?? 0} format={(n) => `${n.toFixed(1)} ms`} icon={<Timer />} accent="magenta" hint={`p95 ${f1(latest.p95_latency_ms)} ms`} />
        </StaggerItem>

        <StaggerItem className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Throughput by mode"
            description="Operations per second, latest run"
            icon={<Zap />}
            table={{ columns: ["Mode", "Ops/s"], rows: chartRows.map((r) => [r.name, r.Throughput]) }}
            empty={chartRows.length === 0 ? "The latest run has no per-mode breakdown." : undefined}
          >
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartRows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <ChartGradients />
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="name" {...axisProps} />
                  <YAxis {...axisProps} />
                  <Tooltip content={<ChartTooltip formatter={(v) => `${v} ops/s`} />} cursor={{ fill: "var(--muted)" }} />
                  <Bar dataKey="Throughput" fill="url(#bar-0)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
          <ChartCard
            title="Latency by mode"
            description="Mean and 95th percentile, milliseconds"
            icon={<Timer />}
            legend={[{ label: "Mean", color: SERIES[1] }, { label: "p95", color: SERIES[2] }]}
            table={{ columns: ["Mode", "Mean ms", "p95 ms"], rows: chartRows.map((r) => [r.name, r.Mean, r.P95]) }}
            empty={chartRows.length === 0 ? "The latest run has no per-mode breakdown." : undefined}
          >
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartRows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <ChartGradients />
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="name" {...axisProps} />
                  <YAxis {...axisProps} />
                  <Tooltip content={<ChartTooltip formatter={(v) => `${v} ms`} />} cursor={{ fill: "var(--muted)" }} />
                  <Bar dataKey="Mean" fill="url(#bar-1)" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="P95" fill="url(#bar-2)" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </StaggerItem>

        <StaggerItem className="grid gap-4">
          <h2 className="font-display text-xl font-semibold">Recent runs</h2>
          {q.data.map((r) => <RunCard key={r.id} run={r} />)}
        </StaggerItem>
      </Stagger>
    </>
  );
}

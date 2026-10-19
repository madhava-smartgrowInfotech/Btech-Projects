import { Activity, Blocks, Gauge, Users, Vote } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps, SERIES } from "@/components/charts/Chart";
import { AuditTable, ChainBadge, Hash, StatusBadge, ValidatorList } from "@/components/domain/common";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";
import { useAdminOverview } from "@/lib/queries";
import type { Block, ElectionStats } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function DashboardSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Loading dashboard">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[132px] rounded-2xl" />)}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-72 rounded-2xl" />
        <Skeleton className="h-72 rounded-2xl" />
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const q = useAdminOverview();
  const navigate = useNavigate();

  const header = (
    <PageHeader
      eyebrow="Administrator"
      title="Admin dashboard"
      description="Monitor elections, turnout, ledger health and system performance."
      actions={
        <Button asChild>
          <Link to="/app/admin/elections">
            <Vote /> Manage elections
          </Link>
        </Button>
      }
    />
  );

  if (q.isPending) return <>{header}<DashboardSkeleton /></>;
  if (q.isError) return <>{header}<ErrorState error={q.error} title="Could not load the dashboard" onRetry={() => q.refetch()} /></>;
  const d = q.data;

  const electionCols: Column<ElectionStats>[] = [
    { key: "title", header: "Election", cell: (e) => <span className="font-medium">{e.title}</span>, sortValue: (e) => e.title },
    { key: "status", header: "Status", cell: (e) => <StatusBadge status={e.status} /> },
    { key: "votes", header: "Votes", cell: (e) => `${e.votes} / ${e.eligible}`, align: "right" },
    { key: "end", header: "Ends", cell: (e) => <span className="text-xs text-muted-foreground">{formatDate(e.end_time, true)}</span>, hideOnCard: true },
  ];
  const blockCols: Column<Block>[] = [
    { key: "i", header: "Block", cell: (b) => <span className="font-medium">#{b.block_index}</span> },
    { key: "hash", header: "Hash", cell: (b) => <Hash value={b.block_hash} /> },
    { key: "tx", header: "Tx", cell: (b) => b.transaction_count, align: "right" },
  ];

  const chartData = [...d.elections].reverse().map((e) => ({
    name: e.title.length > 22 ? `${e.title.slice(0, 21)}…` : e.title,
    Votes: e.votes,
    Eligible: e.eligible,
  }));
  const bench = d.benchmark;

  return (
    <>
      {header}
      <Stagger className="space-y-4">
        <StaggerItem className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Registered voters" value={d.total_voters} icon={<Users />} />
          <StatCard label="Votes cast" value={d.total_votes} icon={<Vote />} accent="cyan" hint={`across ${d.election_count} ${d.election_count === 1 ? "election" : "elections"}`} />
          <StatCard
            label="Ledger height"
            value={d.chain.valid ? (d.chain.height ?? 0) : null}
            icon={<Blocks />}
            accent="magenta"
            hint={<ChainBadge chain={d.chain} />}
          />
          <StatCard label="Elections" value={d.election_count} icon={<Activity />} hint={`${d.open_count} open now`} />
        </StaggerItem>

        <StaggerItem className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
          <ChartCard
            title="Turnout by election"
            description="Ballots cast against eligible voters"
            icon={<Vote />}
            legend={[{ label: "Votes", color: SERIES[0] }, { label: "Eligible", color: SERIES[1] }]}
            table={{ columns: ["Election", "Votes", "Eligible"], rows: chartData.map((r) => [r.name, r.Votes, r.Eligible]) }}
            empty={chartData.length === 0 ? "No elections yet. Create one to see turnout here." : undefined}
          >
            <div style={{ height: Math.max(220, chartData.length * 52 + 32) }} className="w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
                  <ChartGradients />
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={130} {...axisProps} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--muted)" }} />
                  <Bar dataKey="Votes" fill="url(#bar-0)" radius={[0, 8, 8, 0]} barSize={14} />
                  <Bar dataKey="Eligible" fill="url(#bar-1)" radius={[0, 8, 8, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          <Card className="flex flex-col">
            <CardHeader title="Validators" description="3 nodes · quorum 2 of 3" icon={<Activity />} />
            <CardBody className="flex-1">
              {d.validators.length === 0 ? (
                <p className="text-sm text-muted-foreground">No validator nodes are registered yet.</p>
              ) : (
                <ValidatorList validators={d.validators} />
              )}
            </CardBody>
          </Card>
        </StaggerItem>

        <StaggerItem className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader
              title="Recent elections"
              icon={<Vote />}
              action={<Button asChild variant="ghost" size="sm" magnetic={false}><Link to="/app/admin/elections">Manage</Link></Button>}
            />
            <CardBody>
              <Table
                columns={electionCols}
                rows={d.elections.slice(0, 5)}
                rowKey={(e) => e.id}
                pageSize={5}
                caption="Recent elections"
                onRowClick={(e) => navigate(`/app/admin/elections/${e.id}`)}
                empty={
                  <EmptyState
                    icon={<Vote />}
                    title="No elections yet"
                    description="Create the first election and add candidates to start collecting votes."
                    action={<Button asChild><Link to="/app/admin/elections">Create an election</Link></Button>}
                  />
                }
              />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Recent blocks" description={d.chain.valid ? "Chain verified from genesis to tip" : "Chain verification failed"} icon={<Blocks />} />
            <CardBody>
              <Table columns={blockCols} rows={d.blocks} rowKey={(b) => b.block_index} pageSize={5} caption="Recent blocks" />
            </CardBody>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card>
            <CardHeader
              title="Performance"
              description="Latest benchmark run on synthetic voters"
              icon={<Gauge />}
              action={<Button asChild variant="ghost" size="sm" magnetic={false}><Link to="/app/admin/benchmarks">View benchmarks</Link></Button>}
            />
            <CardBody>
              {bench ? (
                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <div className="text-xs text-muted-foreground">Sync throughput</div>
                    <div className="font-display text-2xl font-semibold tabular-nums">{(bench.throughput_sync ?? 0).toFixed(1)} <span className="text-sm font-normal text-muted-foreground">ops/s</span></div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Async throughput</div>
                    <div className="font-display text-2xl font-semibold tabular-nums">{(bench.throughput_async ?? 0).toFixed(1)} <span className="text-sm font-normal text-muted-foreground">ops/s</span></div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Latency (mean / p95)</div>
                    <div className="font-display text-2xl font-semibold tabular-nums">{(bench.mean_latency_ms ?? 0).toFixed(1)} / {(bench.p95_latency_ms ?? 0).toFixed(1)} <span className="text-sm font-normal text-muted-foreground">ms</span></div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No benchmark has been run yet. Run <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">python -m app.benchmarks.run_benchmark</code> and refresh.
                </p>
              )}
            </CardBody>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card>
            <CardHeader title="Recent audit events" icon={<Activity />} action={<Badge tone="neutral">Last {d.audit_logs.length}</Badge>} />
            <CardBody>
              <AuditTable logs={d.audit_logs} pageSize={6} empty={<p className="text-sm text-muted-foreground">No audit events recorded yet.</p>} />
            </CardBody>
          </Card>
        </StaggerItem>
      </Stagger>
    </>
  );
}

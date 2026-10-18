import { useQueryClient } from "@tanstack/react-query";
import { History as HistoryIcon, Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link, useNavigate } from "react-router";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, GlowDot, gridProps } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { riskColor, verdictLabel } from "@/lib/domain";
import { useReviews } from "@/lib/hooks";
import { keys } from "@/lib/queries";
import type { ReviewRow } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const tone = { BLOCK: "danger", REQUEST_CHANGES: "warning", APPROVE: "success" } as const;

export default function HistoryPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useReviews();
  const [search, setSearch] = useState("");
  const [toDelete, setToDelete] = useState<ReviewRow | null>(null);

  const rows = useMemo(() => {
    const n = search.trim().toLowerCase();
    return (q.data ?? []).filter((r) => !n || (r.title + r.source + r.verdict + r.id).toLowerCase().includes(n));
  }, [q.data, search]);

  async function remove(r: ReviewRow) {
    try {
      await api.delete(`/reviews/${r.id}`);
      await qc.invalidateQueries({ queryKey: keys.reviews });
      qc.removeQueries({ queryKey: keys.review(r.id) });
      toast.success(`Deleted “${r.title}”.`);
    } catch (e) {
      toast.error(`Couldn't delete the review: ${errorMessage(e)}`);
      throw e;
    }
  }

  const cols: Column<ReviewRow>[] = [
    { key: "created", header: "Created", cell: (r) => <span className="whitespace-nowrap">{formatDate(r.created, true)}</span>, sortValue: (r) => r.created, hideOnCard: true },
    { key: "title", header: "Title", cell: (r) => <Link to={`/app/review/${r.id}`} onClick={(e) => e.stopPropagation()} className="font-medium hover:underline">{r.title}</Link>, sortValue: (r) => r.title },
    { key: "verdict", header: "Verdict", cell: (r) => <Badge tone={tone[r.verdict]}>{verdictLabel(r.verdict)}</Badge>, sortValue: (r) => r.verdict },
    {
      key: "score",
      header: "Risk",
      cell: (r) => (
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full" style={{ width: `${Math.max(2, r.score)}%`, background: riskColor(r.score) }} /></div>
          <span className="w-7 text-xs tabular-nums">{r.score}</span>
        </div>
      ),
      sortValue: (r) => r.score,
    },
    { key: "security", header: "Security", align: "right", cell: (r) => r.security, sortValue: (r) => r.security },
    { key: "findings", header: "Findings", align: "right", cell: (r) => r.findings, sortValue: (r) => r.findings },
    { key: "id", header: "ID", cell: (r) => <code className="font-mono text-xs text-muted-foreground">{r.id}</code>, hideOnCard: true },
    {
      key: "del",
      header: <span className="sr-only">Delete</span>,
      align: "right",
      cell: (r) => (
        <IconButton label={`Delete ${r.title}`} size="icon-sm" onClick={(e) => { e.stopPropagation(); setToDelete(r); }}>
          <Trash2 />
        </IconButton>
      ),
    },
  ];

  const trend = [...(q.data ?? [])].sort((a, b) => a.created.localeCompare(b.created)).map((r) => ({ t: r.created, score: r.score, title: r.title }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="History"
        title="Review history"
        description="Every review you run is saved. Open one to see its findings, patches and exports again."
        actions={<Button asChild><Link to="/app/review"><Plus /> New review</Link></Button>}
      />

      {q.isPending ? (
        <div className="space-y-4" role="status" aria-label="Loading history">
          <Skeleton className="h-10 w-72" />
          <Skeleton className="h-64" />
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load your history" onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState
          icon={<HistoryIcon />}
          title="No reviews saved yet"
          description="Run the demo pull request or paste your own diff. Each finished review appears here."
          action={<Button onClick={() => navigate("/app/review")}>Run a review</Button>}
        />
      ) : (
        <div className="grid gap-5 2xl:grid-cols-[1.7fr_1fr]">
          <div className="min-w-0 space-y-3">
            <SearchField value={search} onChange={setSearch} label="Search reviews" placeholder="Search title, source, verdict…" className="max-w-sm" />
            {rows.length === 0 ? (
              <EmptyState icon={<HistoryIcon />} title="No reviews match your search" action={<Button variant="secondary" onClick={() => setSearch("")}>Clear search</Button>} />
            ) : (
              <Table columns={cols} rows={rows} rowKey={(r) => r.id} onRowClick={(r) => navigate(`/app/review/${r.id}`)} initialSort={{ key: "created", dir: "desc" }} pageSize={10} caption="Saved reviews" />
            )}
          </div>
          <ChartCard
            title="Risk score over time"
            description="One point per saved review"
            className="h-fit"
            table={{ columns: ["Created", "Title", "Risk"], rows: trend.map((d) => [formatDate(d.t, true), d.title, d.score]) }}
            empty={trend.length < 2 ? "Run at least two reviews to see a trend." : undefined}
          >
            <div className="h-64" role="img" aria-label="Risk score of each saved review over time">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <ChartGradients />
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="t" {...axisProps} tickFormatter={(v: string) => formatDate(v)} minTickGap={32} />
                  <YAxis {...axisProps} domain={[0, 100]} width={32} />
                  <Tooltip content={<ChartTooltip labelFormatter={(l) => formatDate(String(l), true)} />} />
                  <Area type="monotone" dataKey="score" name="Risk" stroke="#7C5CFF" strokeWidth={2.5} fill="url(#area-0)" activeDot={GlowDot("#7C5CFF")} isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>
      )}

      <ConfirmModal
        open={toDelete !== null}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete this review?"
        description={toDelete ? `“${toDelete.title}” is removed from your history for good.` : ""}
        onConfirm={() => (toDelete ? remove(toDelete) : undefined)}
      />
    </div>
  );
}

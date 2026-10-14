import { Link, useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ClipboardList, FileText } from "lucide-react";

import { StageBadge } from "@/components/app/StageBadge";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";
import { api, pct } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { PatientDetail as PatientDetailData, ScreeningSummary } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/utils";

const COLUMNS: Column<ScreeningSummary>[] = [
  {
    key: "id",
    header: "#",
    cell: (s) => (
      <Link className="text-violet-ink hover:underline" to={`/screenings/${s.id}`}>
        #{s.id}
      </Link>
    ),
  },
  { key: "date", header: "Date", cell: (s) => formatDate(s.created_at, true) },
  { key: "eye", header: "Eye", cell: (s) => s.eye || "-" },
  {
    key: "quality",
    header: "Image quality",
    cell: (s) =>
      s.quality_passed ? <Badge tone="success">Passed</Badge> : <Badge tone="warning">Check</Badge>,
  },
  { key: "retina", header: "Retinopathy", cell: (s) => pct(s.retina_prob) },
  { key: "heart", header: "Heart risk", cell: (s) => pct(s.heart_prob) },
  { key: "stage", header: "Stage", cell: (s) => <StageBadge stage={s.stage} /> },
  {
    key: "report",
    header: <span className="sr-only">Report</span>,
    align: "right",
    cell: (s) =>
      s.stage ? (
        <Button variant="ghost" size="icon-sm" asChild>
          <Link to={`/screenings/${s.id}/report`} aria-label={`Report for screening #${s.id}`} title="Report">
            <FileText />
          </Link>
        </Button>
      ) : null,
  },
];

export default function PatientDetail() {
  const { id = "" } = useParams();
  const query = useQuery({
    queryKey: keys.patient(id),
    queryFn: async () => (await api.get<PatientDetailData>(`/patients/${id}`)).data,
    enabled: !!id,
  });
  const p = query.data;
  useBreadcrumb(p?.name ?? null);

  if (query.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading patient">
        <Skeleton className="h-10 w-72" />
        <div className="grid gap-4 sm:grid-cols-3">
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
        </div>
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }
  if (query.isError || !p) {
    return (
      <ErrorState
        error={query.error}
        title="Couldn't open this patient"
        hint={
          <Link to="/patients" className="underline underline-offset-4">
            Back to patients
          </Link>
        }
        onRetry={() => query.refetch()}
      />
    );
  }

  return (
    <div className="space-y-8">
      <Link to="/patients" className="inline-flex items-center gap-1 text-sm text-violet-ink underline-offset-4 hover:underline">
        <ArrowLeft className="size-4" aria-hidden /> All patients
      </Link>
      <PageHeader
        title={p.name}
        description={`${p.code} · ${p.age} years · ${p.sex} · registered ${formatDate(p.created_at)}`}
        actions={
          <Button asChild>
            <Link to={`/screening/new?patient=${p.id}`}>New screening for this patient</Link>
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Screenings" value={p.screenings.length} />
        <StatCard label="Latest stage" display={<StageBadge stage={p.latest_stage} />} />
        <StatCard label="Last screened" display={p.last_screened ? timeAgo(p.last_screened) : "Never"} />
      </div>

      <section aria-labelledby="history-heading" className="space-y-4">
        <h2 id="history-heading" className="font-display text-lg font-semibold">
          Screening history
        </h2>
        <Table<ScreeningSummary>
          caption="Screening history"
          columns={COLUMNS}
          rows={p.screenings}
          rowKey={(s) => s.id}
          empty={
            <Card className="p-0">
              <EmptyState
                icon={<ClipboardList />}
                title="No screenings yet"
                description="Run the first screening for this patient to see results here."
                action={
                  <Button asChild>
                    <Link to={`/screening/new?patient=${p.id}`}>New screening for this patient</Link>
                  </Button>
                }
              />
            </Card>
          }
        />
      </section>
    </div>
  );
}

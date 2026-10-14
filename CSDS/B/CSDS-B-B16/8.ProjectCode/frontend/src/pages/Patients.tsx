import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, Search, Users } from "lucide-react";

import { StageBadge } from "@/components/app/StageBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";
import { SearchField } from "@/components/ui/Field";
import { api, pct } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { PatientSummary, ScreeningSummary } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/utils";

const PATIENT_COLUMNS: Column<PatientSummary>[] = [
  {
    key: "name",
    header: "Patient",
    sortValue: (p) => p.name,
    cell: (p) => (
      <Link className="font-medium text-violet-ink hover:underline" to={`/patients/${p.id}`}>
        {p.name}
      </Link>
    ),
  },
  { key: "code", header: "Code", cell: (p) => <span className="font-mono text-xs">{p.code}</span> },
  { key: "agesex", header: "Age / sex", cell: (p) => `${p.age} / ${p.sex}` },
  {
    key: "screenings",
    header: "Screenings",
    align: "right",
    sortValue: (p) => p.screening_count,
    cell: (p) => p.screening_count,
  },
  {
    key: "last",
    header: "Last screened",
    sortValue: (p) => p.last_screened,
    cell: (p) =>
      p.last_screened ? (
        <span title={formatDate(p.last_screened, true)}>{timeAgo(p.last_screened)}</span>
      ) : (
        <span className="text-muted-foreground">Never</span>
      ),
  },
  { key: "stage", header: "Latest stage", cell: (p) => <StageBadge stage={p.latest_stage} /> },
];

const SCREENING_COLUMNS: Column<ScreeningSummary>[] = [
  {
    key: "id",
    header: "#",
    cell: (s) => (
      <Link className="text-violet-ink hover:underline" to={`/screenings/${s.id}`}>
        #{s.id}
      </Link>
    ),
  },
  { key: "patient", header: "Patient", cell: (s) => s.patient_name },
  { key: "date", header: "Date", cell: (s) => formatDate(s.created_at, true) },
  { key: "retina", header: "Retinopathy", cell: (s) => pct(s.retina_prob) },
  { key: "heart", header: "Heart risk", cell: (s) => pct(s.heart_prob) },
  { key: "stage", header: "Stage", cell: (s) => <StageBadge stage={s.stage} /> },
];

export default function Patients() {
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");

  // Search waits 250 ms after the last keystroke before it calls the API.
  useEffect(() => {
    const t = setTimeout(() => setQ(search.trim()), 250);
    return () => clearTimeout(t);
  }, [search]);

  const patients = useQuery({
    queryKey: keys.patients(q),
    queryFn: async () => (await api.get<PatientSummary[]>("/patients", { params: { q } })).data,
    placeholderData: (previous) => previous,
  });
  const recent = useQuery({
    queryKey: keys.recentScreenings,
    queryFn: async () => (await api.get<ScreeningSummary[]>("/screenings", { params: { limit: 10 } })).data,
  });

  const noPatients = q ? (
    <EmptyState
      icon={<Search />}
      title={`No patients match “${q}”`}
      description="Try a different name or patient code."
      action={
        <Button variant="secondary" size="sm" onClick={() => setSearch("")}>
          Clear search
        </Button>
      }
    />
  ) : (
    <EmptyState
      icon={<Users />}
      title="No patients yet"
      description="Patients are registered when you run a screening for them."
      action={
        <Button asChild>
          <Link to="/screening/new">Start a screening</Link>
        </Button>
      }
    />
  );

  return (
    <div className="space-y-8">
      <PageHeader
        title="Patients & history"
        description="Find a patient to see their screenings, or review the latest results across the clinic."
        actions={
          <Button asChild>
            <Link to="/screening/new">New screening</Link>
          </Button>
        }
      />

      <section aria-labelledby="patients-heading" className="space-y-4">
        <h2 id="patients-heading" className="font-display text-lg font-semibold">
          Patients
        </h2>
        <SearchField value={search} onChange={setSearch} placeholder="Search by name or code" label="Search patients" className="max-w-md" />

        {patients.isPending ? (
          <div className="space-y-2" role="status" aria-label="Loading patients">
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
            <Skeleton className="h-12 w-full rounded-xl" />
          </div>
        ) : patients.isError ? (
          <ErrorState error={patients.error} title="Couldn't load patients" hint="Check that the RetinaGuard API is running." onRetry={() => patients.refetch()} />
        ) : (
          <Table<PatientSummary>
            caption="Patients"
            columns={PATIENT_COLUMNS}
            rows={patients.data}
            rowKey={(p) => p.id}
            initialSort={{ key: "last", dir: "desc" }}
            empty={noPatients}
          />
        )}
      </section>

      <section aria-labelledby="recent-heading" className="space-y-4">
        <h2 id="recent-heading" className="font-display text-lg font-semibold">
          Recent screenings
        </h2>
        {recent.isPending ? (
          <Skeleton className="h-40 w-full rounded-2xl" />
        ) : recent.isError ? (
          <ErrorState error={recent.error} title="Couldn't load recent screenings" onRetry={() => recent.refetch()} />
        ) : (
          <Table<ScreeningSummary>
            caption="Recent screenings"
            columns={SCREENING_COLUMNS}
            rows={recent.data}
            rowKey={(s) => s.id}
            empty={
              <Card className="p-0">
                <EmptyState
                  icon={<ClipboardList />}
                  title="No screenings yet"
                  description="Completed screenings appear here with their findings and stage."
                  action={
                    <Button asChild>
                      <Link to="/screening/new">Start a screening</Link>
                    </Button>
                  }
                />
              </Card>
            }
          />
        )}
      </section>
    </div>
  );
}

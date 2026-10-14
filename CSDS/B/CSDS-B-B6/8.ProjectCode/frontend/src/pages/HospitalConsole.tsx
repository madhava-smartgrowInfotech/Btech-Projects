import { useMutation, useQuery } from "@tanstack/react-query";
import { Building2, ClipboardPlus, Fingerprint, RefreshCcw, Search, Server, UploadCloud } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { FormField, Input, SearchField } from "@/components/ui/Field";
import { CardsSkeleton, EmptyState, ErrorState, toast } from "@/components/ui/Feedback";
import { Modal } from "@/components/ui/Overlay";
import { type Column, Table as DataTable } from "@/components/ui/Table";
import { PageHeader } from "@/components/ui/Layout";
import { Switch } from "@/components/ui/Toggles";
import { api, errorMessage } from "@/lib/api";
import { HOSPITAL_NAMES, HOSPITAL_TONE } from "@/lib/constants";
import { useAuth } from "@/lib/auth";
import { keys, queryClient } from "@/lib/queries";
import type { HospitalPatient, HospitalStatus, MpiPerson, PushedSummary, VisitResult } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

export default function HospitalConsole() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [hkey, setHkey] = useState(user?.hospital ?? "A");

  const hospitals = useQuery({ queryKey: keys.hospitals, queryFn: async () => (await api.get<HospitalStatus[]>("/hospitals")).data });
  const summaries = useQuery({ queryKey: keys.summaries, queryFn: async () => (await api.get<PushedSummary[]>("/sync")).data });

  const current = hospitals.data?.find((h) => h.key === hkey);
  const online = hospitals.data?.filter((h) => h.online).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={isAdmin ? "Platform administrator" : user?.hospital_name ?? "Hospital"}
        title={
          <span className="inline-flex items-center gap-2">
            <Building2 className="size-6 text-violet-ink" aria-hidden />
            {isAdmin ? "Hospitals and patient index" : "Hospital console"}
          </span>
        }
        description="Record treatment at this hospital. The record stays here, and a FHIR summary is pushed to UniHealth."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Hospitals online" value={hospitals.data ? online : null} hint={hospitals.data ? `of ${hospitals.data.length}` : undefined} icon={<Server />} />
        <StatCard
          label={current ? `Patients at ${HOSPITAL_NAMES[hkey]?.split(" ")[0] ?? hkey}` : "Patients"}
          value={current?.online ? (current.counts.Patient ?? 0) : null}
          hint={current && !current.online ? "server offline" : "on this FHIR server"}
          accent="cyan"
          icon={<Search />}
        />
        <StatCard
          label="Summaries received"
          value={summaries.data ? summaries.data.length : null}
          hint="latest 50 shown below"
          accent="magenta"
          icon={<UploadCloud />}
        />
      </div>

      <Card>
        <CardHeader
          icon={<Server />}
          title="FHIR R4 servers"
          description={isAdmin ? "Select a hospital to work on its patients" : "Your hospital's FHIR server"}
          action={
            <Button variant="secondary" size="sm" loading={hospitals.isFetching} onClick={() => hospitals.refetch()}>
              <RefreshCcw /> Refresh
            </Button>
          }
        />
        <CardBody>
          {hospitals.isPending ? (
            <CardsSkeleton count={3} />
          ) : hospitals.isError ? (
            <ErrorState error={hospitals.error} onRetry={() => hospitals.refetch()} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-3">
              {hospitals.data.map((h) => {
                const active = hkey === h.key;
                return (
                  <button
                    key={h.key}
                    type="button"
                    disabled={!isAdmin}
                    onClick={() => setHkey(h.key)}
                    aria-pressed={active}
                    className={cn(
                      "glass rounded-2xl p-4 text-left transition-colors",
                      active && "border-[var(--violet)] ring-1 ring-[var(--violet)]",
                      isAdmin ? "hover:bg-[var(--glass-hover)]" : "cursor-default",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <Badge tone={HOSPITAL_TONE[h.key] ?? "neutral"}>{h.name}</Badge>
                      <span className={cn("shrink-0 text-xs", h.online ? "text-success" : "text-danger")}>
                        ● {h.online ? `FHIR ${h.fhir_version ?? "R4"}` : "offline"}
                      </span>
                    </div>
                    <div className="mt-2 break-all font-mono text-xs text-muted-foreground">{h.base_url}</div>
                    {h.online ? (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {Object.entries(h.counts).map(([t, n]) => (
                          <span key={t} className="rounded-md bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                            {t} {n}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <div className="mt-2 text-xs text-danger">{h.error}</div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <PatientsCard key={hkey} hkey={hkey} hospitalName={HOSPITAL_NAMES[hkey] ?? hkey} />

        <Card>
          <CardHeader icon={<UploadCloud />} title="Summaries pushed to UniHealth" description="Newest first" />
          <CardBody>
            {summaries.isPending ? (
              <CardsSkeleton count={1} className="grid-cols-1" />
            ) : summaries.isError ? (
              <ErrorState error={summaries.error} onRetry={() => summaries.refetch()} />
            ) : summaries.data.length === 0 ? (
              <EmptyState icon={<UploadCloud />} title="No summaries yet" description="Record a visit for a patient to push the first summary." />
            ) : (
              <ul className="space-y-2">
                {summaries.data.slice(0, 12).map((s) => (
                  <li key={s.id} className="rounded-xl border border-[var(--glass-border)] p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <Badge tone={HOSPITAL_TONE[s.hospital] ?? "neutral"}>{s.hospital_name}</Badge>
                      <span className="shrink-0 text-xs text-muted-foreground">{formatDate(s.received_at, true)}</span>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      Patient <span className="font-mono">{s.local_id}</span> → {s.person_id ?? "unlinked"} · {s.entries} FHIR entries
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      {isAdmin && <MpiPanel />}
    </div>
  );
}

function PatientsCard({ hkey, hospitalName }: { hkey: string; hospitalName: string }) {
  const [query, setQuery] = useState("");
  const [applied, setApplied] = useState("");
  const [selected, setSelected] = useState<HospitalPatient | null>(null);
  const [visitOpen, setVisitOpen] = useState(false);

  const patients = useQuery({
    queryKey: keys.hospitalPatients(hkey, applied),
    queryFn: async () => (await api.get<HospitalPatient[]>(`/hospitals/${hkey}/patients`, { params: { q: applied } })).data,
  });

  const push = useMutation({
    mutationFn: (pid: string) => api.post<{ pushed_entries: number; platform: { person_id: string | null } }>(`/hospitals/${hkey}/patients/${pid}/sync`).then((r) => r.data),
    onSuccess: (r) => {
      toast.success(`Summary of ${r.pushed_entries} entries pushed to UniHealth`);
      queryClient.invalidateQueries({ queryKey: keys.summaries });
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const columns: Column<HospitalPatient>[] = [
    { key: "name", header: "Patient", cell: (p) => <span className="font-medium">{p.name || "Unnamed"}</span>, sortValue: (p) => p.name },
    { key: "local", header: "Local ID", cell: (p) => <span className="font-mono text-xs">{p.local_id}</span>, className: "hidden md:table-cell" },
    { key: "dob", header: "Born", cell: (p) => formatDate(p.birth_date), sortValue: (p) => p.birth_date },
    { key: "gender", header: "Gender", cell: (p) => <span className="capitalize">{p.gender || "-"}</span> },
  ];

  const submitFilter = (e: FormEvent) => {
    e.preventDefault();
    setApplied(query.trim());
  };

  return (
    <Card className="lg:col-span-2">
      <CardHeader icon={<Search />} title={`Patients at ${hospitalName}`} description="Select a patient to record a visit" />
      <CardBody className="space-y-4">
        <form className="flex flex-col gap-2 sm:flex-row" onSubmit={submitFilter}>
          <div className="flex-1">
            <SearchField value={query} onChange={setQuery} placeholder="Filter by name" label="Filter patients by name" />
          </div>
          <Button type="submit" variant="secondary" loading={patients.isFetching}>
            Filter
          </Button>
        </form>

        {patients.isPending ? (
          <CardsSkeleton count={2} className="grid-cols-1" />
        ) : patients.isError ? (
          <ErrorState error={patients.error} title="Patients could not be listed" hint="Check that this hospital's FHIR server is running." onRetry={() => patients.refetch()} />
        ) : (
          <DataTable
            caption="Patients at this hospital"
            columns={columns}
            rows={patients.data}
            rowKey={(p) => p.local_id}
            pageSize={8}
            onRowClick={(p) => setSelected(p)}
            empty={<EmptyState icon={<Search />} title="No patients found" description="Clear the filter to see everyone at this hospital." />}
          />
        )}

        {selected && (
          <div className="flex flex-col gap-3 rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="truncate font-medium">{selected.name}</div>
              <div className="text-xs text-muted-foreground">
                <span className="font-mono">{selected.local_id}</span> · {formatDate(selected.birth_date)} · {selected.gender || "-"}
              </div>
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <Button variant="secondary" loading={push.isPending && push.variables === selected.local_id} onClick={() => push.mutate(selected.local_id)}>
                <UploadCloud /> Push summary
              </Button>
              <Button onClick={() => setVisitOpen(true)}>
                <ClipboardPlus /> Record visit
              </Button>
            </div>
          </div>
        )}
      </CardBody>

      {selected && (
        <VisitModal
          open={visitOpen}
          onOpenChange={setVisitOpen}
          hkey={hkey}
          patient={selected}
        />
      )}
    </Card>
  );
}

const EMPTY_VISIT = { visit_type: "Outpatient consultation", diagnosis: "", medication: "", dosage: "", follow_up_days: "30" };

function VisitModal({
  open,
  onOpenChange,
  hkey,
  patient,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  hkey: string;
  patient: HospitalPatient;
}) {
  const [form, setForm] = useState(EMPTY_VISIT);
  const [result, setResult] = useState<VisitResult | null>(null);

  const visit = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post<VisitResult>(`/hospitals/${hkey}/visits`, body).then((r) => r.data),
    onSuccess: (r) => {
      setResult(r);
      toast.success("Visit recorded and summary pushed");
      queryClient.invalidateQueries({ queryKey: keys.summaries });
      queryClient.invalidateQueries({ queryKey: keys.hospitals });
    },
  });

  const set = (k: keyof typeof EMPTY_VISIT) => (e: ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  return (
    <Modal
      open={open}
      onOpenChange={(v) => {
        if (!visit.isPending) onOpenChange(v);
        if (!v) {
          setResult(null);
          visit.reset();
        }
      }}
      title={`Record visit for ${patient.name}`}
      description="Saved as FHIR resources at this hospital. A summary is then pushed to UniHealth."
      footer={
        result ? (
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        ) : (
          <>
            <Button variant="secondary" onClick={() => onOpenChange(false)} disabled={visit.isPending}>
              Cancel
            </Button>
            <Button type="submit" form="visit-form" loading={visit.isPending}>
              <RefreshCcw /> Record visit and sync summary
            </Button>
          </>
        )
      }
    >
      {result ? (
        <div role="status" className="space-y-2 rounded-xl border border-success/30 bg-success/10 p-4 text-sm">
          <div className="font-medium text-success">Saved {result.created.entry.length} FHIR resources at this hospital.</div>
          <p className="text-foreground/85">
            Pushed a summary of {result.sync.pushed_entries} entries to UniHealth
            {result.sync.platform.person_id ? ` (person ${result.sync.platform.person_id})` : ""}; {result.sync.platform.reminders_added} reminder
            {result.sync.platform.reminders_added === 1 ? "" : "s"} created for the patient.
          </p>
        </div>
      ) : (
        <form
          id="visit-form"
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            visit.mutate({
              ...form,
              patient_id: patient.local_id,
              follow_up_days: Number(form.follow_up_days) || null,
              medication: form.medication,
              dosage: form.dosage,
            });
          }}
        >
          <FormField label="Visit type">{(p) => <Input {...p} value={form.visit_type} onChange={set("visit_type")} />}</FormField>
          <FormField label="Diagnosis" hint="e.g. Essential hypertension">
            {(p) => <Input {...p} value={form.diagnosis} onChange={set("diagnosis")} required />}
          </FormField>
          <FormField label="Medication (optional)" hint="e.g. Amlodipine 5 MG Oral Tablet">
            {(p) => <Input {...p} value={form.medication} onChange={set("medication")} />}
          </FormField>
          <FormField label="Dosage (optional)" hint="e.g. 1 tablet every morning">
            {(p) => <Input {...p} value={form.dosage} onChange={set("dosage")} />}
          </FormField>
          <FormField label="Follow-up in (days)" hint="Leave empty for no follow-up">
            {(p) => <Input {...p} type="number" min={1} value={form.follow_up_days} onChange={set("follow_up_days")} />}
          </FormField>
          {visit.isError && (
            <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] p-3 text-sm text-danger">
              {errorMessage(visit.error)}
            </p>
          )}
        </form>
      )}
    </Modal>
  );
}

function MpiPanel() {
  const [linkedOnly, setLinkedOnly] = useState(true);
  const persons = useQuery({ queryKey: keys.mpiPersons, queryFn: async () => (await api.get<MpiPerson[]>("/mpi/persons")).data });

  const rebuild = useMutation({
    mutationFn: () => api.post<{ records: number; persons: number; linked_persons: number }>("/mpi/rebuild").then((r) => r.data),
    onSuccess: (r) => {
      toast.success(`Linked ${r.records} hospital records into ${r.persons} persons`);
      queryClient.invalidateQueries({ queryKey: keys.mpiPersons });
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const shown = (persons.data ?? []).filter((p) => !linkedOnly || p.links.length > 1);

  const columns: Column<MpiPerson>[] = [
    {
      key: "person",
      header: "Person",
      cell: (p) => (
        <div>
          <div className="font-medium">{p.name}</div>
          <div className="font-mono text-xs text-muted-foreground">{p.person_id}</div>
        </div>
      ),
      sortValue: (p) => p.name,
    },
    {
      key: "links",
      header: "Hospital records (name as recorded, DOB, phone, confidence)",
      cell: (p) => (
        <div className="space-y-1">
          {p.links.map((l) => (
            <div key={l.local_id} className="flex flex-wrap items-center gap-2 text-xs">
              <Badge tone={HOSPITAL_TONE[l.hospital] ?? "neutral"}>{l.hospital}</Badge>
              <span className="font-mono">{l.local_id}</span>
              <span>{l.name}</span>
              <span className="text-muted-foreground">{formatDate(l.birth_date)}</span>
              <span className="text-muted-foreground">{l.phone || "no phone"}</span>
              <span className={cn("font-semibold", l.confidence >= 0.95 ? "text-success" : "text-warning")}>{Math.round(l.confidence * 100)}%</span>
            </div>
          ))}
        </div>
      ),
    },
  ];

  return (
    <Card>
      <CardHeader
        icon={<Fingerprint />}
        title="Master Patient Index"
        description="Hospital records linked into one person"
        action={
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Switch checked={linkedOnly} onCheckedChange={setLinkedOnly} aria-label="Show linked people only" />
              Linked only
            </label>
            <Button variant="secondary" size="sm" loading={rebuild.isPending} onClick={() => rebuild.mutate()}>
              <RefreshCcw /> Re-run linkage
            </Button>
          </div>
        }
      />
      <CardBody>
        {persons.isPending ? (
          <CardsSkeleton count={1} className="grid-cols-1" />
        ) : persons.isError ? (
          <ErrorState error={persons.error} onRetry={() => persons.refetch()} />
        ) : (
          <DataTable
            caption="Master Patient Index"
            columns={columns}
            rows={shown}
            rowKey={(p) => p.person_id}
            pageSize={8}
            empty={<EmptyState icon={<Fingerprint />} title="No linked people yet" description="Turn off Linked only to see every person, or re-run linkage." />}
          />
        )}
      </CardBody>
    </Card>
  );
}

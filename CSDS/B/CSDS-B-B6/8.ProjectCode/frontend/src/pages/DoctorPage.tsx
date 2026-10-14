import { useMutation, useQuery } from "@tanstack/react-query";
import { Lock, Search, Stethoscope, UserRound } from "lucide-react";
import { lazy, Suspense, useState } from "react";

import { AssistantPanel } from "@/components/records/AssistantPanel";
import { RecordSources } from "@/components/records/RecordSources";
import { RecordTimeline } from "@/components/records/RecordTimeline";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Input } from "@/components/ui/Field";
import { CardsSkeleton, EmptyState, ErrorState, InlineLoader, ProgressBar, toast } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { api, errorMessage, statusOf } from "@/lib/api";
import { HOSPITAL_TONE } from "@/lib/constants";
import { useAuth } from "@/lib/auth";
import { keys, queryClient } from "@/lib/queries";
import type { MpiSearchResult, RecordView } from "@/lib/types";
import { cn } from "@/lib/utils";

// Charts are heavy: the risk panel is fetched only when this page first renders it.
const RiskPanel = lazy(() => import("@/components/records/RiskPanel"));

interface SearchForm {
  name: string;
  birth_date: string;
}

export default function DoctorPage() {
  const { user } = useAuth();
  const [form, setForm] = useState<SearchForm>({ name: "", birth_date: "" });
  const [submitted, setSubmitted] = useState<SearchForm | null>(null);
  const [selected, setSelected] = useState<MpiSearchResult | null>(null);
  const [reason, setReason] = useState("Continuity of care");
  const [record, setRecord] = useState<RecordView | null>(null);
  const [blocked, setBlocked] = useState<string | null>(null);

  const search = useQuery({
    queryKey: keys.mpiSearch(submitted?.name ?? "", submitted?.birth_date ?? ""),
    queryFn: async () =>
      (await api.get<MpiSearchResult[]>("/mpi/search", { params: { q: submitted?.name ?? "", birth_date: submitted?.birth_date ?? "" } })).data,
    enabled: submitted !== null,
  });

  const access = useMutation({
    mutationFn: (body: { person_id: string; reason: string }) => api.post<RecordView>("/access/request", body).then((r) => r.data),
    onSuccess: (data) => {
      setRecord(data);
      setBlocked(null);
      queryClient.invalidateQueries({ queryKey: keys.audit });
      toast.success("Records merged from every hospital that has consented");
    },
    onError: (e) => {
      setRecord(null);
      if (statusOf(e) === 403) setBlocked(errorMessage(e));
      else toast.error(errorMessage(e));
    },
  });

  const pick = (p: MpiSearchResult) => {
    setSelected(p);
    setRecord(null);
    setBlocked(null);
    access.reset();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={user?.hospital_name ?? "Clinician"}
        title={
          <span className="inline-flex items-center gap-2">
            <Stethoscope className="size-6 text-violet-ink" aria-hidden /> Patient lookup
          </span>
        }
        description="Search the Master Patient Index, then request a patient's history from every hospital that has consented."
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Card>
            <CardHeader icon={<Search />} title="Find a patient" />
            <CardBody>
              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  setSubmitted({ ...form });
                }}
              >
                <FormField label="Name" hint="Part of a name is enough">
                  {(p) => <Input {...p} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Gibson" />}
                </FormField>
                <FormField label="Date of birth (optional)">
                  {(p) => <Input {...p} type="date" value={form.birth_date} onChange={(e) => setForm({ ...form, birth_date: e.target.value })} />}
                </FormField>
                <Button type="submit" className="w-full" loading={search.isFetching}>
                  Search
                </Button>
              </form>
            </CardBody>
          </Card>

          <div aria-live="polite">
            {submitted === null ? null : search.isPending ? (
              <CardsSkeleton count={2} className="grid-cols-1" />
            ) : search.isError ? (
              <ErrorState error={search.error} title="Search failed" hint="The platform could not reach the hospital index." onRetry={() => search.refetch()} />
            ) : search.data.length === 0 ? (
              <EmptyState icon={<Search />} title="No matching person" description="Check the spelling, or search without a date of birth." />
            ) : (
              <ul className="space-y-2">
                {search.data.map((p) => {
                  const isSelected = selected?.person_id === p.person_id;
                  return (
                    <li key={p.person_id}>
                      <button
                        type="button"
                        onClick={() => pick(p)}
                        aria-pressed={isSelected}
                        className={cn(
                          "glass w-full rounded-2xl p-3 text-left transition-colors hover:border-[color-mix(in_srgb,var(--violet)_40%,var(--glass-border))]",
                          isSelected && "border-[var(--cyan)] ring-1 ring-[var(--cyan)]",
                        )}
                      >
                        <div className="font-medium">{p.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatBirth(p.birth_date)} · {p.gender || "-"} · <span className="font-mono">{p.person_id}</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {p.hospitals.map((h) => (
                            <Badge key={h.key} tone={HOSPITAL_TONE[h.key] ?? "neutral"}>
                              {h.name.split(" ")[0]} {Math.round(h.confidence * 100)}%
                            </Badge>
                          ))}
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        <div className="space-y-4 lg:col-span-2">
          {!selected ? (
            <EmptyState
              icon={<UserRound />}
              title="No patient selected"
              description="Search for a patient on the left, then request access to their history from other hospitals."
            />
          ) : (
            <Card>
              <CardHeader icon={<UserRound />} title={`Request history - ${selected.name}`} />
              <CardBody className="space-y-3">
                <form
                  className="flex flex-col gap-3 sm:flex-row sm:items-end"
                  onSubmit={(e) => {
                    e.preventDefault();
                    access.mutate({ person_id: selected.person_id, reason });
                  }}
                >
                  <FormField label="Clinical reason" className="flex-1">
                    {(p) => <Input {...p} value={reason} onChange={(e) => setReason(e.target.value)} required />}
                  </FormField>
                  <Button type="submit" loading={access.isPending}>
                    {record ? "Refresh record" : "Request history"}
                  </Button>
                </form>
                <p className="text-xs text-muted-foreground">
                  Checked against the patient's consent for {user?.hospital_name ?? "your hospital"}. Every request is written to the audit ledger.
                </p>
                {blocked && (
                  <div role="alert" className="flex items-start gap-2 rounded-xl border border-warning/35 bg-warning/10 p-3 text-sm text-warning">
                    <Lock className="mt-0.5 size-4 shrink-0" aria-hidden />
                    <div>
                      <div className="font-medium">Access blocked</div>
                      <div className="text-foreground/85">
                        {blocked} The request now appears in the patient's consent screen.
                      </div>
                    </div>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {access.isPending && (
            <div className="space-y-2" aria-live="polite">
              <InlineLoader label="Checking consent and fetching FHIR records from each hospital..." />
              <ProgressBar value={0} indeterminate label="Fetching records" />
            </div>
          )}

          {selected && record && !access.isPending && (
            <>
              <RecordSources record={record} personId={selected.person_id} />
              <Suspense fallback={<CardsSkeleton count={2} className="grid-cols-1" />}>
                <RiskPanel personId={selected.person_id} />
              </Suspense>
              <RecordTimeline items={record.timeline} />
              <AssistantPanel personId={selected.person_id} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function formatBirth(value: string) {
  return value || "DOB unknown";
}

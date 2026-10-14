import { useMutation, useQuery } from "@tanstack/react-query";
import { Activity, Bell, Bot, Clock, FileJson, ShieldCheck, ShieldOff } from "lucide-react";
import { useState } from "react";

import { AssistantPanel } from "@/components/records/AssistantPanel";
import { RecordSources } from "@/components/records/RecordSources";
import { RecordTimeline } from "@/components/records/RecordTimeline";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Checkbox } from "@/components/ui/Toggles";
import { FormField, Input } from "@/components/ui/Field";
import { StatCard } from "@/components/ui/Display";
import { CardsSkeleton, EmptyState, ErrorState, toast } from "@/components/ui/Feedback";
import { ConfirmModal, Modal } from "@/components/ui/Overlay";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { api, errorMessage } from "@/lib/api";
import { CATEGORIES, CATEGORY_LABEL, HOSPITAL_NAMES, HOSPITAL_TONE, REMINDER_KIND_LABEL } from "@/lib/constants";
import { useAuth } from "@/lib/auth";
import { keys, queryClient } from "@/lib/queries";
import type { AccessRequest, Consent, RecordView, Reminder, TimelineItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Select } from "@/components/ui/Select";

const STATE_TONE: Record<Reminder["state"], BadgeTone> = {
  overdue: "danger",
  "due today": "warning",
  upcoming: "info",
  done: "success",
};

export default function PatientPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState("timeline");
  const [report, setReport] = useState<TimelineItem | null>(null);

  const record = useQuery({
    queryKey: keys.record("me"),
    queryFn: async () => (await api.get<RecordView>("/records/me")).data,
  });
  const consents = useQuery({ queryKey: keys.consents, queryFn: async () => (await api.get<Consent[]>("/consents")).data });
  const reminders = useQuery({ queryKey: keys.reminders, queryFn: async () => (await api.get<Reminder[]>("/reminders")).data });

  const onlineSources = record.data?.sources.filter((s) => s.status === "online").length ?? 0;
  const activeConsents = consents.data?.filter((c) => c.status === "active").length;
  const openReminders = reminders.data?.filter((r) => !r.done).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="My health record"
        title={record.data?.person.name ?? user?.display_name ?? "My health record"}
        description={
          record.data
            ? `Born ${formatDate(record.data.person.birth_date)} · ${record.data.person.gender} · UniHealth ID ${record.data.person.id}`
            : "Your records from every connected hospital, in one timeline."
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Hospitals connected"
          value={record.data ? onlineSources : null}
          hint={record.data ? `of ${record.data.sources.length} matched to you` : "Loading"}
          icon={<Activity />}
        />
        <StatCard label="Timeline entries" value={record.data ? record.data.timeline.length : null} hint="across all hospitals" />
        <StatCard
          label="Active consents"
          value={activeConsents ?? null}
          hint={`${openReminders} open reminder${openReminders === 1 ? "" : "s"}`}
          accent="cyan"
        />
      </div>

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "timeline", label: "Timeline", icon: <Activity /> },
          { value: "consents", label: "Consents", icon: <ShieldCheck /> },
          { value: "assistant", label: "Assistant", icon: <Bot /> },
          { value: "reminders", label: "Reminders", icon: <Bell />, count: openReminders || undefined },
        ]}
      >
        <TabPanel value="timeline">
          {record.isPending ? (
            <CardsSkeleton count={2} />
          ) : record.isError ? (
            <ErrorState
              error={record.error}
              title="Could not load your record"
              hint="Check that the hospital servers are running, then try again."
              onRetry={() => record.refetch()}
            />
          ) : (
            <div className="space-y-4">
              <RecordSources record={record.data} personId="me" />
              <RecordTimeline
                items={record.data.timeline}
                onExplain={(item) => {
                  setReport(item);
                  setTab("assistant");
                }}
              />
            </div>
          )}
        </TabPanel>

        <TabPanel value="consents">
          <ConsentsTab />
        </TabPanel>

        <TabPanel value="assistant">
          <AssistantPanel personId="me" report={report} onClearReport={() => setReport(null)} />
        </TabPanel>

        <TabPanel value="reminders">
          <RemindersTab />
        </TabPanel>
      </Tabs>
    </div>
  );
}

function invalidateConsents() {
  queryClient.invalidateQueries({ queryKey: keys.consents });
  queryClient.invalidateQueries({ queryKey: keys.accessRequests });
  queryClient.invalidateQueries({ queryKey: keys.record("me") });
}

function ConsentsTab() {
  const consents = useQuery({ queryKey: keys.consents, queryFn: async () => (await api.get<Consent[]>("/consents")).data });
  const requests = useQuery({
    queryKey: keys.accessRequests,
    queryFn: async () => (await api.get<AccessRequest[]>("/access/requests")).data,
  });

  const [hospital, setHospital] = useState("B");
  const [categories, setCategories] = useState<string[]>([...CATEGORIES]);
  const [days, setDays] = useState("90");
  const [fhirOf, setFhirOf] = useState<Consent | null>(null);
  const [revoking, setRevoking] = useState<Consent | null>(null);

  const grant = useMutation({
    mutationFn: (body: { hospital: string; categories: string[]; days: number | null }) =>
      api.post<Consent>("/consents", body).then((r) => r.data),
    onSuccess: (c) => {
      toast.success(`Access granted to ${c.hospital_name}`);
      invalidateConsents();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.post<Consent>(`/consents/${id}/revoke`).then((r) => r.data),
    onSuccess: (c) => {
      toast.success(`Access to ${c.hospital_name} revoked`);
      invalidateConsents();
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  const toggleCategory = (c: string, on: boolean) =>
    setCategories((cur) => (on ? [...cur, c] : cur.filter((x) => x !== c)));

  // Only the newest blocked request per hospital gets an approve button (as before).
  const blocked = requests.data?.filter((r) => r.status === "blocked") ?? [];
  const newestBlockedIds = new Set(
    Object.values(
      blocked.reduce<Record<string, AccessRequest>>((acc, r) => {
        if (!acc[r.hospital]) acc[r.hospital] = r;
        return acc;
      }, {}),
    ).map((r) => r.id),
  );

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="space-y-4">
        <Card>
          <CardHeader icon={<ShieldCheck />} title="Grant access" description="Choose a hospital and what it may see" />
          <CardBody className="space-y-4">
            <FormField label="Hospital">
              {(p) => (
                <Select
                  id={p.id}
                  value={hospital}
                  onValueChange={setHospital}
                  options={Object.entries(HOSPITAL_NAMES).map(([k, n]) => ({ value: k, label: n }))}
                />
              )}
            </FormField>
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">Data categories</legend>
              <div className="grid grid-cols-2 gap-2">
                {CATEGORIES.map((c) => (
                  <label key={c} className="flex cursor-pointer items-center gap-2 text-sm">
                    <Checkbox checked={categories.includes(c)} onCheckedChange={(on) => toggleCategory(c, on)} aria-label={CATEGORY_LABEL[c]} />
                    {CATEGORY_LABEL[c]}
                  </label>
                ))}
              </div>
            </fieldset>
            <FormField label="Valid for (days, empty = no expiry)" hint="Default 90 days">
              {(p) => <Input {...p} type="number" min={1} value={days} onChange={(e) => setDays(e.target.value)} />}
            </FormField>
            <Button
              className="w-full"
              loading={grant.isPending}
              disabled={categories.length === 0}
              onClick={() => grant.mutate({ hospital, categories, days: Number(days) || null })}
            >
              Grant consent
            </Button>
          </CardBody>
        </Card>

        <Card>
          <CardHeader icon={<Clock />} title="Access requests" description="Doctors who asked for your record" />
          <CardBody>
            {requests.isPending ? (
              <CardsSkeleton count={1} className="grid-cols-1" />
            ) : requests.isError ? (
              <ErrorState error={requests.error} onRetry={() => requests.refetch()} />
            ) : requests.data.length === 0 ? (
              <p className="text-sm text-muted-foreground">No doctor has requested your record yet.</p>
            ) : (
              <ul className="space-y-2">
                {requests.data.slice(0, 10).map((r) => (
                  <li key={r.id} className="rounded-xl border border-[var(--glass-border)] p-3 text-sm">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium">{r.doctor}</span>
                      <Badge tone={r.status === "blocked" ? "warning" : "success"}>{r.status === "blocked" ? "awaiting you" : r.status}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {r.reason} · {r.hospital_name} · {formatDate(r.created_at, true)}
                    </div>
                    {newestBlockedIds.has(r.id) && (
                      <Button
                        size="sm"
                        className="mt-2"
                        loading={grant.isPending && grant.variables?.hospital === r.hospital}
                        onClick={() => grant.mutate({ hospital: r.hospital, categories: [...CATEGORIES], days: 90 })}
                      >
                        Approve for {r.hospital_name}
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <Card className="lg:col-span-2">
        <CardHeader icon={<ShieldCheck />} title="My consents" description="Stored as FHIR Consent resources. Revoking takes effect at once." />
        <CardBody>
          {consents.isPending ? (
            <CardsSkeleton count={2} />
          ) : consents.isError ? (
            <ErrorState error={consents.error} onRetry={() => consents.refetch()} />
          ) : consents.data.length === 0 ? (
            <EmptyState
              icon={<ShieldCheck />}
              title="No consents yet"
              description="Doctors from other hospitals cannot see your record until you grant access. Use the form beside this list."
            />
          ) : (
            <ul className="space-y-3">
              {consents.data.map((c) => {
                const active = c.status === "active";
                return (
                  <li
                    key={c.id}
                    className={`rounded-xl border p-4 ${active ? "border-[color-mix(in_srgb,var(--cyan)_40%,var(--glass-border))] bg-[color-mix(in_srgb,var(--cyan)_6%,transparent)]" : "border-[var(--glass-border)] opacity-75"}`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge tone={HOSPITAL_TONE[c.hospital] ?? "neutral"}>{c.hospital_name}</Badge>
                        <Badge tone={active ? "success" : "neutral"}>{c.status}</Badge>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={() => setFhirOf(c)}>
                          <FileJson /> FHIR
                        </Button>
                        {active && (
                          <Button variant="danger" size="sm" onClick={() => setRevoking(c)}>
                            <ShieldOff /> Revoke
                          </Button>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {c.categories.map((x) => (
                        <Badge key={x}>{CATEGORY_LABEL[x] ?? x}</Badge>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Granted {formatDate(c.created_at)} · {c.expires ? `expires ${formatDate(c.expires)}` : "no expiry"}
                      {!active ? ` · revoked ${formatDate(c.updated_at)}` : ""}
                    </p>
                  </li>
                );
              })}
            </ul>
          )}
        </CardBody>
      </Card>

      <Modal
        open={fhirOf !== null}
        onOpenChange={(open) => !open && setFhirOf(null)}
        title="FHIR Consent resource"
        description={fhirOf ? `${fhirOf.hospital_name} · ${fhirOf.status}` : undefined}
      >
        <pre className="scrollbar-thin max-h-96 overflow-auto rounded-xl bg-[#0B0F1A] p-4 text-xs text-slate-100">
          {fhirOf ? JSON.stringify(fhirOf.fhir, null, 2) : ""}
        </pre>
      </Modal>

      <ConfirmModal
        open={revoking !== null}
        onOpenChange={(open) => !open && setRevoking(null)}
        title={`Revoke access to ${revoking?.hospital_name ?? "this hospital"}?`}
        description="Doctors at this hospital will be blocked again at once. The change is written to the audit ledger."
        confirmLabel="Revoke access"
        onConfirm={async () => {
          if (!revoking) return;
          try {
            await revoke.mutateAsync(revoking.id);
          } catch {
            /* the mutation already showed the error */
          }
        }}
      />
    </div>
  );
}

function RemindersTab() {
  const list = useQuery({ queryKey: keys.reminders, queryFn: async () => (await api.get<Reminder[]>("/reminders")).data });
  const [text, setText] = useState("");
  const [due, setDue] = useState(() => new Date().toISOString().slice(0, 10));

  const toggle = useMutation({
    mutationFn: (id: number) => api.post<Reminder[]>(`/reminders/${id}/toggle`).then((r) => r.data),
    onSuccess: (data) => queryClient.setQueryData(keys.reminders, data),
    onError: (e) => toast.error(errorMessage(e)),
  });

  const add = useMutation({
    mutationFn: (body: { text: string; due: string }) => api.post<Reminder[]>("/reminders", body).then((r) => r.data),
    onSuccess: (data) => {
      queryClient.setQueryData(keys.reminders, data);
      setText("");
      toast.success("Reminder added");
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader icon={<Bell />} title="Reminders" description="Medication and follow-up reminders appear here from your treatment plans" />
        <CardBody>
          {list.isPending ? (
            <CardsSkeleton count={1} className="grid-cols-1" />
          ) : list.isError ? (
            <ErrorState error={list.error} onRetry={() => list.refetch()} />
          ) : list.data.length === 0 ? (
            <EmptyState
              icon={<Bell />}
              title="No reminders yet"
              description="They appear from active prescriptions and follow-up plans. You can also add your own."
            />
          ) : (
            <ul className="divide-y divide-[var(--glass-border)]">
              {list.data.map((r) => (
                <li key={r.id} className="flex items-center gap-3 py-3">
                  <Checkbox
                    checked={r.done}
                    disabled={toggle.isPending && toggle.variables === r.id}
                    onCheckedChange={() => toggle.mutate(r.id)}
                    aria-label={`Mark "${r.text}" done`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className={`truncate text-sm ${r.done ? "text-muted-foreground line-through" : "font-medium"}`}>{r.text}</div>
                    <div className="text-xs text-muted-foreground">
                      {REMINDER_KIND_LABEL[r.kind] ?? r.kind} · {r.source}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <Badge tone={STATE_TONE[r.state]}>{r.state}</Badge>
                    <div className="mt-0.5 text-xs text-muted-foreground">{formatDate(r.due)}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader icon={<Clock />} title="Add a reminder" />
        <CardBody>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (text.trim()) add.mutate({ text: text.trim(), due });
            }}
          >
            <FormField label="What" hint="e.g. Book blood test">
              {(p) => <Input {...p} value={text} onChange={(e) => setText(e.target.value)} required />}
            </FormField>
            <FormField label="Due">
              {(p) => <Input {...p} type="date" value={due} onChange={(e) => setDue(e.target.value)} required />}
            </FormField>
            <Button type="submit" className="w-full" loading={add.isPending} disabled={!text.trim()}>
              Add reminder
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}

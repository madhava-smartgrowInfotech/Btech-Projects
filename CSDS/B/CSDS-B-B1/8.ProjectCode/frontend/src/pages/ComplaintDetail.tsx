import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Brain, Check, Circle, MapPin, MessageSquare, RefreshCw, Send, Sparkles, User, WandSparkles } from "lucide-react";
import { lazy, Suspense, useState } from "react";
import { Link, useParams } from "react-router";

import { PriorityBadge, SampleBadge, SlaFlag, StatusBadge } from "@/components/domain/Badges";
import { CategoryWords, PriorityFactors, TimeFactors } from "@/components/domain/Explain";
import { RetrainPanel } from "@/components/domain/RetrainPanel";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Timeline } from "@/components/ui/Display";
import { Input, Textarea, Label } from "@/components/ui/Field";
import { ErrorState, InlineLoader, Skeleton } from "@/components/ui/Feedback";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { toast } from "@/components/ui/Toast";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { SlideUp } from "@/components/motion/SlideUp";
import { api, errorMessage } from "@/lib/api";
import { days, fmtDate, pct } from "@/lib/format";
import { keys, useComplaint, useMeta } from "@/lib/queries";
import type { ComplaintDetail as Detail, Priority } from "@/lib/types";

const PinMap = lazy(() => import("@/components/map/PinMap"));

type Field = "category" | "department" | "priority";
const FIELDS: { key: Field; label: string }[] = [
  { key: "category", label: "Category" },
  { key: "department", label: "Department" },
  { key: "priority", label: "Priority" },
];
const PRIORITIES: Priority[] = ["Low", "Medium", "High", "Critical"];

/** Every mutation on this page returns the refreshed complaint; keep the cache and the lists in step. */
function useDetailUpdater(id: number) {
  const qc = useQueryClient();
  return (data?: Detail) => {
    if (data) qc.setQueryData(keys.detail(id), data);
    else qc.invalidateQueries({ queryKey: keys.detail(id) });
    qc.invalidateQueries({ queryKey: ["queue"] });
    qc.invalidateQueries({ queryKey: ["analytics"] });
  };
}

function Extraction({ c }: { c: Detail }) {
  const refresh = useDetailUpdater(c.id);
  const ex = c.extraction;
  const run = useMutation({
    mutationFn: async () => (await api.post(`/complaints/${c.id}/extract`)).data,
    onSuccess: () => {
      refresh();
      toast.success("Key details extracted");
    },
    onError: (err) => toast.error("Extraction failed", { description: errorMessage(err) }),
  });
  const pending = c.extraction_status === "pending";
  return (
    <Card>
      <CardHeader
        title="Key details (Gemini)"
        description="Place, issue and hazards pulled out of the text."
        icon={<Sparkles />}
        action={
          !pending && (
            <Button variant="secondary" size="sm" magnetic={false} onClick={() => run.mutate()} loading={run.isPending}>
              {!run.isPending && <Sparkles />} {c.extraction_status === "done" ? "Re-run" : "Extract details"}
            </Button>
          )
        }
      />
      <CardBody>
        {pending ? (
          <InlineLoader label="Extracting details…" />
        ) : c.extraction_status === "done" && ex ? (
          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
            {(
              [
                ["Place", ex.place],
                ["Issue", ex.issue],
                ["Affected people", ex.affected_people],
                ["Since", ex.duration],
                ["Hazards", ex.hazards?.length ? ex.hazards.join(", ") : null],
              ] as [string, string | null | undefined][]
            ).map(([k, v]) => (
              <div key={k}>
                <dt className="text-xs text-muted-foreground">{k}</dt>
                <dd>{v || <span className="text-muted-foreground">not mentioned</span>}</dd>
              </div>
            ))}
            <div className="sm:col-span-2">
              <dt className="text-xs text-muted-foreground">Summary</dt>
              <dd>{ex.summary_en}</dd>
            </div>
          </dl>
        ) : c.extraction_status === "failed" ? (
          <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] px-3 py-2 text-sm text-danger">
            Extraction failed: {ex?.error || "unknown error"}. Use “Extract details” to try again; everything else still works without it.
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">Not extracted yet.</p>
        )}
      </CardBody>
    </Card>
  );
}

function Explanations({ c }: { c: Detail }) {
  const [tab, setTab] = useState("category");
  const ex = c.ai.explanations ?? {};
  return (
    <Card>
      <CardHeader
        title="Why the AI suggested this"
        description={`Explanations from model v${c.ai.explained_with_version || c.ai.model_version}.`}
        icon={<Brain />}
      />
      <CardBody>
        <Tabs
          value={tab}
          onValueChange={setTab}
          tabs={[
            { value: "category", label: "Category" },
            { value: "priority", label: "Priority" },
            { value: "time", label: "Time" },
          ]}
        >
          <TabPanel value="category">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Words that drove the category (LIME)</h3>
            <p className="mb-3 text-sm text-muted-foreground">
              Suggested <b className="text-foreground">{c.ai.category}</b> ({pct(c.ai.category_confidence)})
            </p>
            <CategoryWords words={ex.category_words} category={c.ai.category} />
          </TabPanel>
          <TabPanel value="priority">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Factors behind the priority (SHAP)</h3>
            <p className="mb-3 text-sm text-muted-foreground">
              Suggested <b className="text-foreground">{c.ai.priority}</b> ({pct(c.ai.priority_confidence)})
            </p>
            <PriorityFactors data={ex.priority_factors} />
          </TabPanel>
          <TabPanel value="time">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Factors behind the time estimate (SHAP)</h3>
            <p className="mb-3 text-sm text-muted-foreground">
              Expected <b className="text-foreground">~{days(c.ai.expected_days)}</b>, learned from real service-request resolution times
            </p>
            <TimeFactors data={ex.time_factors} />
          </TabPanel>
        </Tabs>
      </CardBody>
    </Card>
  );
}

function Suggestion({ c, meta, onOverride }: { c: Detail; meta: ReturnType<typeof useMeta>["data"]; onOverride: () => void }) {
  const ai = c.ai;
  const refresh = useDetailUpdater(c.id);
  const decided = !!c.final.department;
  const closed = c.status === "Resolved" || c.status === "Rejected";
  const [editing, setEditing] = useState(!decided);
  const [values, setValues] = useState<Record<Field, string>>({
    category: c.final.category || ai.category,
    department: c.final.department || ai.department,
    priority: c.final.priority || ai.priority,
  });
  const [reasons, setReasons] = useState<Partial<Record<Field, string>>>({});
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const options: Record<Field, string[]> = {
    category: meta?.categories.map((x) => x.name) ?? [],
    department: meta?.departments.map((x) => x.name) ?? [],
    priority: PRIORITIES,
  };
  const conf: Record<Field, number> = { category: ai.category_confidence, department: ai.department_confidence, priority: ai.priority_confidence };
  const alts: Record<Field, { label: string; p: number }[]> = {
    category: ai.category_top3 ?? [],
    department: ai.department_top3 ?? [],
    priority: Object.entries(ai.priority_proba ?? {})
      .map(([label, p]) => ({ label, p }))
      .sort((a, b) => b.p - a.p),
  };
  const changed = FIELDS.filter((f) => values[f.key] !== ai[f.key]);

  const save = useMutation({
    mutationFn: async () => (await api.post<Detail>(`/complaints/${c.id}/decision`, { ...values, reasons, note })).data,
    onMutate: () => setError(""),
    onSuccess: (data) => {
      refresh(data);
      if (changed.length) onOverride();
      toast.success(changed.length ? `Saved with ${changed.length} override${changed.length > 1 ? "s" : ""}` : "Suggestion accepted and complaint assigned");
      setEditing(false);
      setReasons({});
      setNote("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  return (
    <Card strong>
      <CardHeader
        title="AI suggestion & your decision"
        icon={<Brain />}
        action={
          decided &&
          !closed &&
          !editing && (
            <Button variant="secondary" size="sm" magnetic={false} onClick={() => setEditing(true)}>
              Change decision
            </Button>
          )
        }
      />
      <CardBody>
        {decided && !editing ? (
          <div className="space-y-2.5 text-sm">
            {FIELDS.map((f) => (
              <div key={f.key} className="flex items-center justify-between gap-2">
                <span className="text-muted-foreground">{f.label}</span>
                <span className="flex flex-wrap items-center justify-end gap-2 font-medium">
                  {f.key === "priority" ? <PriorityBadge priority={c.final.priority} /> : c.final[f.key]}
                  {c.final[f.key] !== ai[f.key] && <Badge tone="warning">overridden</Badge>}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Expected time</span>
              <span className="font-medium">~{days(c.final.expected_days)}</span>
            </div>
            <p className="pt-1 text-xs text-muted-foreground">
              Decided by {c.final.reviewed_by} · {fmtDate(c.final.reviewed_at)}
            </p>
          </div>
        ) : (
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            {FIELDS.map((f) => {
              const isChanged = values[f.key] !== ai[f.key];
              return (
                <div key={f.key} className="space-y-1.5">
                  <div className="flex items-baseline justify-between gap-2">
                    <Label htmlFor={`sel-${f.key}`}>{f.label}</Label>
                    <span className="text-xs text-muted-foreground">
                      AI: <b className="text-foreground">{ai[f.key]}</b> ({pct(conf[f.key])})
                    </span>
                  </div>
                  <Select
                    id={`sel-${f.key}`}
                    value={values[f.key]}
                    onValueChange={(v) => setValues({ ...values, [f.key]: v })}
                    options={options[f.key].map((o) => ({ value: o, label: o }))}
                  />
                  <div className="flex flex-wrap gap-x-3 text-[11px] text-muted-foreground">
                    {alts[f.key].slice(0, 3).map((a) => (
                      <span key={a.label}>
                        {a.label} {pct(a.p)}
                      </span>
                    ))}
                  </div>
                  {isChanged && (
                    <Input
                      aria-label={`Why change the ${f.label.toLowerCase()}?`}
                      placeholder={`Why change the ${f.label.toLowerCase()}? (required - becomes a training label)`}
                      value={reasons[f.key] ?? ""}
                      onChange={(e) => setReasons({ ...reasons, [f.key]: e.target.value })}
                      required
                      minLength={3}
                    />
                  )}
                </div>
              );
            })}
            <div className="glass-flat space-y-1 rounded-xl p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Expected time to resolve</span>
                <span className="font-semibold">~{days(ai.expected_days)}</span>
              </div>
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>SLA {c.current.sla_days} days</span>
                <SlaFlag risk={c.current.sla_breach_risk} breached={c.current.sla_breached && !closed} />
              </div>
              {changed.some((f) => f.key !== "department") && <p className="text-xs text-muted-foreground">Time will be re-estimated for your category / priority.</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="citizen-note">Note for the citizen (optional)</Label>
              <Input id="citizen-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Shown on their status timeline" />
            </div>
            {error && (
              <p role="alert" className="text-sm text-danger">
                {error}
              </p>
            )}
            <div className="flex gap-2">
              <Button type="submit" className="flex-1" loading={save.isPending} disabled={!meta}>
                {!save.isPending && <Check />}
                {changed.length ? `Save with ${changed.length} override${changed.length > 1 ? "s" : ""}` : "Accept & assign"}
              </Button>
              {decided && (
                <Button type="button" variant="secondary" magnetic={false} onClick={() => setEditing(false)}>
                  Cancel
                </Button>
              )}
            </div>
          </form>
        )}
      </CardBody>
    </Card>
  );
}

function StatusActions({ c }: { c: Detail }) {
  const refresh = useDetailUpdater(c.id);
  const [note, setNote] = useState("");
  const [confirmReject, setConfirmReject] = useState(false);
  const [error, setError] = useState("");
  const decided = !!c.final.department;

  const set = useMutation({
    mutationFn: async (status: "In Progress" | "Resolved" | "Rejected") => (await api.post<Detail>(`/complaints/${c.id}/status`, { status, note })).data,
    onMutate: () => setError(""),
    onSuccess: (data, status) => {
      refresh(data);
      setNote("");
      toast.success(status === "Rejected" ? "Complaint rejected - the citizen was told why" : `Marked ${status.toLowerCase()}`);
    },
    onError: (err) => setError(errorMessage(err)),
  });

  if (c.status === "Resolved" || c.status === "Rejected") return null;
  const busy = set.isPending;
  return (
    <Card>
      <CardHeader title="Update status" icon={<RefreshCw />} />
      <CardBody className="space-y-3">
        <Label htmlFor="status-note" className="sr-only">
          Update for the citizen
        </Label>
        <Textarea
          id="status-note"
          className="min-h-16"
          placeholder="Update for the citizen (optional; required to reject)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          {c.status !== "In Progress" && (
            <Button variant="secondary" magnetic={false} disabled={!decided || busy} onClick={() => set.mutate("In Progress")}>
              In progress
            </Button>
          )}
          <Button disabled={!decided || busy} loading={busy && set.variables === "Resolved"} onClick={() => set.mutate("Resolved")}>
            Mark resolved
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => (note.trim().length < 3 ? setError("Please give the citizen a reason for rejecting the complaint.") : setConfirmReject(true))}
          >
            Reject
          </Button>
        </div>
        {!decided && <p className="text-xs text-muted-foreground">Accept or override the AI suggestion first.</p>}
        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        )}
      </CardBody>
      <ConfirmModal
        open={confirmReject}
        onOpenChange={setConfirmReject}
        title="Reject this complaint?"
        description={`The complaint is closed and the citizen sees this reason: “${note.trim()}”. This cannot be undone.`}
        confirmLabel="Reject complaint"
        onConfirm={() => set.mutateAsync("Rejected")}
      />
    </Card>
  );
}

function ReplyBox({ c }: { c: Detail }) {
  const refresh = useDetailUpdater(c.id);
  const [note, setNote] = useState("");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");

  const makeDraft = useMutation({
    mutationFn: async () => (await api.post<{ draft: string }>(`/complaints/${c.id}/draft-reply`, { note })).data.draft,
    onMutate: () => setError(""),
    onSuccess: (d) => {
      setDraft(d);
      toast.success(`Draft ready in ${c.language} - edit it before sending`);
    },
    onError: (err) => setError(errorMessage(err)),
  });
  const send = useMutation({
    mutationFn: async () => (await api.post<Detail>(`/complaints/${c.id}/reply`, { message: draft })).data,
    onMutate: () => setError(""),
    onSuccess: (data) => {
      refresh(data);
      setDraft("");
      setNote("");
      toast.success("Reply sent - the citizen sees it on their status page");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  return (
    <Card>
      <CardHeader title={`Reply to citizen (${c.language})`} icon={<MessageSquare />} />
      <CardBody className="space-y-3">
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            aria-label="What should the reply mention?"
            placeholder="What should the reply mention? (optional)"
            wrapperClassName="flex-1"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <Button variant="secondary" magnetic={false} onClick={() => makeDraft.mutate()} loading={makeDraft.isPending} disabled={send.isPending}>
            {!makeDraft.isPending && <WandSparkles />} Draft with Gemini
          </Button>
        </div>
        <Label htmlFor="reply-text" className="sr-only">
          Reply message
        </Label>
        <Textarea
          id="reply-text"
          className="min-h-32"
          placeholder="Write a reply or generate a draft, then edit it before sending."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        {error && (
          <p role="alert" className="text-sm text-danger">
            {error}
            {makeDraft.isError && " You can still write the reply yourself."}
          </p>
        )}
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">The citizen sees this on their status page.</span>
          <Button onClick={() => send.mutate()} loading={send.isPending} disabled={draft.trim().length < 5 || makeDraft.isPending}>
            {!send.isPending && <Send />} Send
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]" role="status" aria-label="Loading complaint and explanations">
      <div className="space-y-5">
        {[40, 28, 56].map((h, i) => (
          <div key={i} className="glass space-y-3 rounded-2xl p-5">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className={h > 50 ? "h-28 w-full" : h > 30 ? "h-20 w-full" : "h-14 w-full"} />
          </div>
        ))}
      </div>
      <div className="space-y-5">
        {[0, 1].map((i) => (
          <div key={i} className="glass space-y-3 rounded-2xl p-5">
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ComplaintDetail() {
  const { id } = useParams();
  const q = useComplaint(id);
  const meta = useMeta();
  const [overrode, setOverrode] = useState(false);
  const c = q.data;
  useBreadcrumb(c?.tracking_id);

  return (
    <div>
      <Link to="/app/queue" className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft className="size-4" /> Back to the queue
      </Link>

      {q.isPending ? (
        <div className="mt-4">
          <DetailSkeleton />
        </div>
      ) : q.isError || !c ? (
        <ErrorState className="mt-4" error={q.error} title="Couldn't open this complaint" hint="It may have been removed, or the server is busy." onRetry={() => q.refetch()} />
      ) : (
        <SlideUp>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <h1 className="font-mono text-xl font-semibold sm:text-2xl">{c.tracking_id}</h1>
            <StatusBadge status={c.status} />
            <PriorityBadge priority={c.current.priority} />
            <SampleBadge show={c.is_sample} />
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <div className="space-y-5">
              <Card>
                <CardHeader title="Complaint" icon={<User />} />
                <CardBody className="space-y-4">
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>{c.citizen}</span>
                    <span>{fmtDate(c.created_at)}</span>
                    <span>{c.language}</span>
                    <span className="inline-flex items-center gap-1">
                      <MapPin className="size-3.5" /> {c.ward || "No location"}
                    </span>
                  </div>
                  <p className="whitespace-pre-line text-[15px] leading-relaxed" lang={c.language === "Hindi" ? "hi" : undefined}>
                    {c.text}
                  </p>
                  {(c.photo_url || c.lat != null) && (
                    <div className="grid gap-3 sm:grid-cols-2">
                      {c.photo_url && <img src={c.photo_url} alt="Photo attached to the complaint" className="h-44 w-full rounded-xl border border-[var(--glass-border)] object-cover" />}
                      {c.lat != null && c.lng != null && (
                        <div className="h-44 overflow-hidden rounded-xl border border-[var(--glass-border)]">
                          <Suspense fallback={<Skeleton className="h-full w-full" />}>
                            <PinMap lat={c.lat} lng={c.lng} />
                          </Suspense>
                        </div>
                      )}
                    </div>
                  )}
                </CardBody>
              </Card>

              <Extraction c={c} />
              <Explanations c={c} />

              <Card>
                <CardHeader title="Activity" description="Everything that happened on this complaint." icon={<RefreshCw />} />
                <CardBody>
                  <Timeline
                    items={c.events.map((e) => ({
                      icon: e.kind === "reply" ? <MessageSquare /> : <Circle />,
                      title: (
                        <span className="flex flex-wrap items-center gap-2">
                          {e.kind === "status" ? <StatusBadge status={e.status} /> : <span className="capitalize">{e.kind}</span>}
                          {!e.public && <Badge tone="neutral">internal</Badge>}
                          {e.actor && <span className="text-xs font-normal text-muted-foreground">{e.actor}</span>}
                        </span>
                      ),
                      meta: fmtDate(e.at),
                      body: e.message ? <span className="whitespace-pre-line text-foreground/80">{e.message}</span> : undefined,
                    }))}
                  />
                </CardBody>
              </Card>
            </div>

            <div className="space-y-5">
              <Suggestion
                key={`${c.id}-${c.final.department ?? "open"}-${c.final.reviewed_at ?? ""}`}
                c={c}
                meta={meta.data}
                onOverride={() => setOverrode(true)}
              />
              <StatusActions key={`${c.id}-${c.status}`} c={c} />
              <ReplyBox key={c.id} c={c} />
              <RetrainPanel highlight={overrode} />
            </div>
          </div>
        </SlideUp>
      )}
    </div>
  );
}

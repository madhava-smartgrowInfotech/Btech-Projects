import { ArrowLeft, CalendarClock, Plus, UserCheck, UserX, Users, Vote } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router";

import { ResultsView } from "@/components/domain/ResultsView";
import { StatusActions } from "@/components/domain/StatusActions";
import { StatusBadge, formatPct } from "@/components/domain/common";
import { Stagger, StaggerItem } from "@/components/motion";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input, Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Overlay";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAddCandidate, useAdminElection, useToggleCandidate } from "@/lib/queries";
import type { Candidate } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function AddCandidateModal({ electionId, open, onOpenChange }: { electionId: number; open: boolean; onOpenChange: (o: boolean) => void }) {
  const add = useAddCandidate(electionId);
  const [form, setForm] = useState({ name: "", party: "", description: "", manifesto: "" });
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const c = await add.mutateAsync({ ...form, name: form.name.trim(), party: form.party.trim() });
      toast.success(`${c.name} added as a candidate`);
      setForm({ name: "", party: "", description: "", manifesto: "" });
      onOpenChange(false);
    } catch (err) {
      setError(errorMessage(err, "Could not add the candidate."));
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Add a candidate"
      description="Candidates appear on the ballot as soon as the election is open."
      footer={
        <>
          <Button variant="secondary" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button type="submit" form="add-candidate" loading={add.isPending} disabled={!form.name.trim() || !form.party.trim()}>Add candidate</Button>
        </>
      }
    >
      <form id="add-candidate" onSubmit={submit} className="space-y-4">
        {error && <div role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        <FormField label="Name">{(p) => <Input {...p} required maxLength={128} value={form.name} onChange={set("name")} placeholder="Full name" />}</FormField>
        <FormField label="Party or organization">{(p) => <Input {...p} required maxLength={128} value={form.party} onChange={set("party")} placeholder="Party or independent" />}</FormField>
        <FormField label="Description" hint="Optional one-line summary.">{(p) => <Input {...p} value={form.description} onChange={set("description")} />}</FormField>
        <FormField label="Manifesto" hint="Optional. Shown to voters on the ballot.">{(p) => <Textarea {...p} value={form.manifesto} onChange={set("manifesto")} />}</FormField>
      </form>
    </Modal>
  );
}

function CandidateCard({ c }: { c: Candidate }) {
  const toggle = useToggleCandidate();
  async function run() {
    try {
      const updated = await toggle.mutateAsync(c.id);
      toast.success(`${updated.name} is now ${updated.is_active ? "active" : "inactive"}`);
    } catch (err) {
      toast.error(errorMessage(err, "Could not update the candidate."));
    }
  }
  return (
    <Card className="flex h-full flex-col gap-3 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display font-semibold leading-tight">{c.name}</h3>
          <p className="text-sm text-muted-foreground">{c.party}</p>
        </div>
        <Badge tone={c.is_active ? "success" : "warning"}>{c.is_active ? "Active" : "Inactive"}</Badge>
      </div>
      {c.description && <p className="text-sm">{c.description}</p>}
      {c.manifesto && <p className="text-sm text-muted-foreground">{c.manifesto}</p>}
      <Button size="sm" variant="secondary" className="mt-auto self-start" loading={toggle.isPending} onClick={run}>
        {c.is_active ? <><UserX /> Deactivate</> : <><UserCheck /> Activate</>}
      </Button>
    </Card>
  );
}

export default function AdminElectionDetail() {
  const id = Number(useParams().id);
  const q = useAdminElection(id);
  const [open, setOpen] = useState(false);
  useBreadcrumb(q.data?.election.title);

  if (q.isPending) {
    return (
      <div className="space-y-4" role="status" aria-label="Loading election">
        <Skeleton className="h-16 w-2/3 rounded-xl" />
        <div className="grid gap-4 sm:grid-cols-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-[132px] rounded-2xl" />)}</div>
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    );
  }
  if (q.isError) {
    return (
      <ErrorState
        error={q.error}
        title="Could not load this election"
        hint="It may have been removed."
        onRetry={() => q.refetch()}
      />
    );
  }

  const { election: e, candidates, eligible, votes, turnout, results } = q.data;
  return (
    <>
      <PageHeader
        eyebrow={<Link to="/app/admin/elections" className="inline-flex items-center gap-1 hover:underline"><ArrowLeft className="size-3.5" /> All elections</Link>}
        title={e.title}
        description={
          <span className="flex flex-col gap-2">
            {e.description && <span>{e.description}</span>}
            <span className="inline-flex flex-wrap items-center gap-3 text-xs">
              <StatusBadge status={e.status} />
              <span className="inline-flex items-center gap-1.5"><CalendarClock className="size-3.5" /> {formatDate(e.start_time, true)} to {formatDate(e.end_time, true)}</span>
            </span>
          </span>
        }
        actions={<StatusActions id={e.id} title={e.title} status={e.status} />}
      />
      <Stagger className="space-y-6">
        <StaggerItem className="grid gap-4 sm:grid-cols-3">
          <StatCard label="Eligible voters" value={eligible} icon={<Users />} />
          <StatCard label="Votes cast" value={votes} icon={<Vote />} accent="cyan" />
          <StatCard label="Turnout" value={turnout} format={(n) => formatPct(n)} icon={<UserCheck />} accent="magenta" />
        </StaggerItem>

        <StaggerItem>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-xl font-semibold">Candidates <span className="text-base font-normal text-muted-foreground">({candidates.length})</span></h2>
            <Button onClick={() => setOpen(true)}><Plus /> Add candidate</Button>
          </div>
          <AddCandidateModal electionId={id} open={open} onOpenChange={setOpen} />
          {candidates.length === 0 ? (
            <EmptyState
              icon={<Users />}
              title="No candidates yet"
              description="Voters can only vote once at least one active candidate is on the ballot."
              action={<Button onClick={() => setOpen(true)}><Plus /> Add the first candidate</Button>}
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {candidates.map((c) => <CandidateCard key={c.id} c={c} />)}
            </div>
          )}
        </StaggerItem>

        {results && (
          <StaggerItem>
            <h2 className="mb-3 font-display text-xl font-semibold">Results</h2>
            <ResultsView tally={results} />
          </StaggerItem>
        )}
      </Stagger>
    </>
  );
}

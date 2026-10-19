import { CalendarClock, Plus, Users, Vote } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { StatusActions } from "@/components/domain/StatusActions";
import { StatusBadge } from "@/components/domain/common";
import { Stagger, StaggerItem } from "@/components/motion";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input, Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Overlay";
import { ProgressBar } from "@/components/ui/Feedback";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAdminElections, useCreateElection } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

/** datetime-local value (browser time) for a Date. */
function localInput(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** The API stores naive UTC; convert what the user typed (local time) to that. */
function toApiUtc(local: string) {
  return new Date(local).toISOString().slice(0, 19);
}

function CreateElectionModal({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const create = useCreateElection();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [start, setStart] = useState(() => localInput(new Date()));
  const [end, setEnd] = useState(() => localInput(new Date(Date.now() + 7 * 864e5)));
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (new Date(end) <= new Date(start)) {
      setError("The end time must be after the start time.");
      return;
    }
    try {
      const created = await create.mutateAsync({ title: title.trim(), description: description.trim(), start_time: toApiUtc(start), end_time: toApiUtc(end) });
      toast.success(`Election "${created.title}" created as a draft. Add candidates, then open it.`);
      setTitle("");
      setDescription("");
      onOpenChange(false);
    } catch (err) {
      setError(errorMessage(err, "Could not create the election."));
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Create an election"
      description="It starts as a draft. Every registered voter is made eligible automatically."
      footer={
        <>
          <Button variant="secondary" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button type="submit" form="create-election" loading={create.isPending} disabled={!title.trim()}>Create election</Button>
        </>
      }
    >
      <form id="create-election" onSubmit={submit} className="space-y-4">
        {error && <div role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
        <FormField label="Title">
          {(p) => <Input {...p} required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Campus Council Election 2027" />}
        </FormField>
        <FormField label="Description" hint="Optional. Shown to voters.">
          {(p) => <Textarea {...p} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What is this election for?" />}
        </FormField>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Starts">
            {(p) => <Input {...p} type="datetime-local" required value={start} onChange={(e) => setStart(e.target.value)} />}
          </FormField>
          <FormField label="Ends">
            {(p) => <Input {...p} type="datetime-local" required value={end} onChange={(e) => setEnd(e.target.value)} />}
          </FormField>
        </div>
      </form>
    </Modal>
  );
}

export default function AdminElections() {
  const q = useAdminElections();
  const [open, setOpen] = useState(false);

  const header = (
    <PageHeader
      eyebrow="Administrator"
      title="Elections"
      description="Create elections, manage candidates and control when voting is open."
      actions={<Button onClick={() => setOpen(true)}><Plus /> New election</Button>}
    />
  );

  return (
    <>
      {header}
      <CreateElectionModal open={open} onOpenChange={setOpen} />
      {q.isPending ? (
        <div className="grid gap-4 lg:grid-cols-2" role="status" aria-label="Loading elections">
          {[0, 1].map((i) => <Skeleton key={i} className="h-48 rounded-2xl" />)}
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Could not load elections" onRetry={() => q.refetch()} />
      ) : q.data.length === 0 ? (
        <EmptyState
          icon={<Vote />}
          title="No elections yet"
          description="Create your first election, add candidates, then open it for voting."
          action={<Button onClick={() => setOpen(true)}><Plus /> Create an election</Button>}
        />
      ) : (
        <Stagger className="grid gap-4 lg:grid-cols-2">
          {q.data.map((e) => (
            <StaggerItem key={e.id}>
              <Card className="flex h-full flex-col gap-4 p-5">
                <div className="flex items-start justify-between gap-3">
                  <Link to={`/app/admin/elections/${e.id}`} className="min-w-0 rounded-lg hover:underline">
                    <h2 className="font-display text-lg font-semibold leading-tight">{e.title}</h2>
                  </Link>
                  <StatusBadge status={e.status} />
                </div>
                {e.description && <p className="text-sm text-muted-foreground">{e.description}</p>}
                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <CalendarClock className="size-3.5 shrink-0" /> {formatDate(e.start_time, true)} to {formatDate(e.end_time, true)}
                </p>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1"><Users className="size-3.5" /> {e.votes} of {e.eligible} voted</span>
                    <span className="tabular-nums">{e.turnout.toFixed(1)}%</span>
                  </div>
                  <ProgressBar value={e.turnout} label={`Turnout for ${e.title}`} />
                </div>
                <div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-[var(--glass-border)] pt-4">
                  <StatusActions id={e.id} title={e.title} status={e.status} />
                  <Button asChild size="sm" variant="outline" magnetic={false}>
                    <Link to={`/app/admin/elections/${e.id}`}>Manage ({e.candidate_count ?? 0})</Link>
                  </Button>
                </div>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>
      )}
    </>
  );
}

import { useMutation } from "@tanstack/react-query";
import { CalendarDays, CheckCircle2, IndianRupee, Plus, Save, Target, Trash2 } from "lucide-react";
import { useState } from "react";

import { Meter } from "@/components/common/Meter";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal, Modal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type Goal } from "@/lib/api";
import { addDaysISO, pct, todayISO, useMoney } from "@/lib/format";
import { useGoals, useMeta, useRefreshData } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

function NewGoalModal({ open, onOpenChange, presets }: { open: boolean; onOpenChange: (o: boolean) => void; presets: string[] }) {
  const money = useMoney();
  const refresh = useRefreshData();
  const blank = () => ({ preset: "Emergency Fund", custom: "", target: "", current: "", date: addDaysISO(todayISO(), 180) });
  const [f, setF] = useState(blank);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const name = f.preset === "Other" ? f.custom.trim() : f.preset;

  const add = useMutation({
    mutationFn: async () => api.post("/goals", { goal_name: name, target_amount: Number(f.target), current_amount: Number(f.current || 0), target_date: f.date }),
    onSuccess: async () => {
      toast.success(`Goal “${name}” created`, { description: `Target ${money(Number(f.target))}` });
      setF(blank());
      onOpenChange(false);
      await refresh();
    },
    onError: (e) => toast.error("Could not create the goal", { description: errorMessage(e) }),
  });

  function submit() {
    const next: Record<string, string> = {};
    if (!name) next.custom = "Please provide a goal name.";
    if (!(Number(f.target) > 0)) next.target = "Target amount must be greater than zero.";
    if (Number(f.current) < 0) next.current = "Savings cannot be negative.";
    if (!f.date) next.date = "Pick a target date.";
    setErrors(next);
    if (!Object.keys(next).length) add.mutate();
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="New savings goal"
      description="We will work out the monthly saving it needs."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit} loading={add.isPending}>
            <Plus /> Create goal
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <FormField label="Goal">
          {(p) => <Select {...p} icon={<Target />} value={f.preset} onValueChange={(v) => setF({ ...f, preset: v })} options={presets.map((g) => ({ value: g, label: g }))} />}
        </FormField>
        {f.preset === "Other" && (
          <FormField label="Goal name" error={errors.custom}>
            {(p) => <Input {...p} autoFocus value={f.custom} onChange={(e) => setF({ ...f, custom: e.target.value })} placeholder="e.g. Wedding fund" />}
          </FormField>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField label="Target amount" error={errors.target}>
            {(p) => <Input {...p} type="number" min="0" step="1000" icon={<IndianRupee />} value={f.target} onChange={(e) => setF({ ...f, target: e.target.value })} />}
          </FormField>
          <FormField label="Saved so far" error={errors.current}>
            {(p) => <Input {...p} type="number" min="0" step="500" icon={<IndianRupee />} value={f.current} onChange={(e) => setF({ ...f, current: e.target.value })} placeholder="0" />}
          </FormField>
        </div>
        <FormField label="Target date" error={errors.date}>
          {(p) => <Input {...p} type="date" icon={<CalendarDays />} min={todayISO()} value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} />}
        </FormField>
      </div>
    </Modal>
  );
}

function GoalCard({ goal, onDelete }: { goal: Goal; onDelete: () => void }) {
  const money = useMoney();
  const refresh = useRefreshData();
  const [amount, setAmount] = useState(String(goal.current_amount));
  const dirty = Number(amount) !== goal.current_amount;
  const update = useMutation({
    mutationFn: async () => api.put(`/goals/${goal.id}`, { current_amount: Number(amount) }),
    onSuccess: async () => {
      toast.success(Number(amount) >= goal.target_amount ? `“${goal.goal_name}” reached. Congratulations!` : "Progress updated");
      await refresh();
    },
    onError: (e) => toast.error("Could not update the goal", { description: errorMessage(e) }),
  });
  const done = goal.status === "completed" || goal.percent_complete >= 100;

  return (
    <Card className="flex h-full flex-col gap-4 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display text-lg font-semibold">{goal.goal_name}</h3>
          <p className="text-sm text-muted-foreground">Target date {formatDate(`${goal.target_date}T00:00:00Z`)}</p>
        </div>
        <div className="flex items-center gap-1">
          <Badge tone={done ? "success" : "violet"}>{done ? "Completed" : goal.status}</Badge>
          <IconButton label={`Delete ${goal.goal_name}`} size="icon-sm" onClick={onDelete}>
            <Trash2 className="text-danger" />
          </IconButton>
        </div>
      </div>
      <div>
        <div className="mb-1.5 flex items-baseline justify-between">
          <span className="font-display text-3xl font-semibold tabular-nums">{pct(goal.percent_complete)}</span>
          <span className="text-sm text-muted-foreground tabular-nums">
            {money(goal.current_amount)} / {money(goal.target_amount)}
          </span>
        </div>
        <Meter value={goal.percent_complete} tone="good" label={`${goal.goal_name} progress`} />
      </div>
      <p className="text-sm text-muted-foreground">
        {done ? (
          <span className="inline-flex items-center gap-1.5 text-success">
            <CheckCircle2 className="size-4" /> You have reached this goal.
          </span>
        ) : (
          <>
            Suggested saving: <strong className="text-foreground">{money(goal.required_monthly_savings)}</strong> per month
          </>
        )}
      </p>
      <form
        className="mt-auto flex items-end gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (Number(amount) >= 0) update.mutate();
        }}
      >
        <FormField label="Update saved amount" className="flex-1">
          {(p) => <Input {...p} type="number" min="0" step="500" value={amount} onChange={(e) => setAmount(e.target.value)} />}
        </FormField>
        <Button type="submit" variant="secondary" loading={update.isPending} disabled={!dirty || !(Number(amount) >= 0)}>
          <Save /> Update
        </Button>
      </form>
    </Card>
  );
}

export default function Goals() {
  const q = useGoals();
  const meta = useMeta();
  const refresh = useRefreshData();
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState<Goal | null>(null);
  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/goals/${id}`),
    onSuccess: async () => {
      toast.success("Goal deleted");
      await refresh();
    },
    onError: (e) => toast.error("Could not delete the goal", { description: errorMessage(e) }),
  });

  const newButton = (
    <Button onClick={() => setOpen(true)}>
      <Plus /> New goal
    </Button>
  );

  return (
    <>
      <PageHeader title="Financial goals" description="Name what you are saving for, and see exactly how much to set aside each month." actions={newButton} />
      {q.isPending ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" role="status" aria-label="Loading goals">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-2xl" />
          ))}
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load your goals" onRetry={() => void q.refetch()} />
      ) : q.data.items.length === 0 ? (
        <EmptyState icon={<Target />} title="No goals yet" description="Add one to start tracking progress, like an emergency fund, a new laptop or a holiday." action={newButton} />
      ) : (
        <Stagger className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {q.data.items.map((g) => (
            <StaggerItem key={g.id}>
              <GoalCard goal={g} onDelete={() => setDeleting(g)} />
            </StaggerItem>
          ))}
        </Stagger>
      )}

      <NewGoalModal open={open} onOpenChange={setOpen} presets={meta.data?.goal_presets ?? ["New Laptop", "Education", "Emergency Fund", "Vacation", "Car", "House", "Other"]} />
      {deleting && (
        <ConfirmModal
          open
          onOpenChange={(o) => !o && setDeleting(null)}
          title={`Delete “${deleting.goal_name}”?`}
          description="The goal and its progress will be removed permanently."
          onConfirm={async () => {
            await remove.mutateAsync(deleting.id);
            setDeleting(null);
          }}
        />
      )}
    </>
  );
}

import { useMutation } from "@tanstack/react-query";
import { CalendarDays, IndianRupee, Save, Tags, Trash2, Wallet } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Meter, meterTone } from "@/components/common/Meter";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type BudgetStatus } from "@/lib/api";
import { MONTHS, useMoney } from "@/lib/format";
import { useBudgets, useMeta, useRefreshData } from "@/lib/queries";
import { cn } from "@/lib/utils";

export default function Budgets() {
  const money = useMoney();
  const refresh = useRefreshData();
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [category, setCategory] = useState("");
  const [amount, setAmount] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [deleting, setDeleting] = useState<BudgetStatus | null>(null);
  const meta = useMeta();
  const q = useBudgets(month, year);
  const yearOk = year >= 2000 && year <= 2100;

  const save = useMutation({
    mutationFn: async () => api.post("/budgets", { category, budget_amount: Number(amount), month, year }),
    onSuccess: async () => {
      toast.success(`Budget for ${category} set to ${money.exact(Number(amount))}`);
      setAmount("");
      await refresh();
    },
    onError: (e) => toast.error("Could not save the budget", { description: errorMessage(e) }),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!category) next.category = "Choose a category.";
    if (!(Number(amount) > 0)) next.amount = "Budget must be greater than zero.";
    if (!yearOk) next.year = "Enter a year between 2000 and 2100.";
    setErrors(next);
    if (!Object.keys(next).length) save.mutate();
  }

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/budgets/${id}`),
    onSuccess: async () => {
      toast.success("Budget deleted");
      await refresh();
    },
    onError: (e) => toast.error("Could not delete the budget", { description: errorMessage(e) }),
  });

  return (
    <>
      <PageHeader title="Budgets" description="Set a monthly limit per category. You will be warned at 75%, 90% and 100%." />
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <Card className="h-fit">
          <CardHeader title="Set a budget" description="Saving again for the same category and month updates it." icon={<Wallet />} />
          <CardBody>
            <form onSubmit={submit} className="space-y-4" noValidate>
              <div className="grid grid-cols-[1fr_6.5rem] gap-3">
                <FormField label="Month">
                  {(p) => <Select {...p} icon={<CalendarDays />} value={String(month)} onValueChange={(v) => setMonth(Number(v))} options={MONTHS.map((m, i) => ({ value: String(i + 1), label: m }))} />}
                </FormField>
                <FormField label="Year" error={errors.year}>
                  {(p) => <Input {...p} type="number" min={2000} max={2100} value={year} onChange={(e) => setYear(Number(e.target.value))} />}
                </FormField>
              </div>
              <FormField label="Category" error={errors.category}>
                {(p) => (
                  <Select
                    {...p}
                    icon={<Tags />}
                    placeholder="Choose a category"
                    value={category}
                    onValueChange={setCategory}
                    options={(meta.data?.categories ?? []).map((c) => ({ value: c, label: c }))}
                  />
                )}
              </FormField>
              <FormField label="Budget amount" error={errors.amount}>
                {(p) => <Input {...p} type="number" min="0" step="100" icon={<IndianRupee />} placeholder="e.g. 6000" value={amount} onChange={(e) => setAmount(e.target.value)} />}
              </FormField>
              <Button type="submit" className="w-full" loading={save.isPending} disabled={meta.isPending}>
                <Save /> Save budget
              </Button>
            </form>
          </CardBody>
        </Card>

        <section aria-label={`Budget status for ${MONTHS[month - 1]} ${year}`} className="space-y-4">
          <h2 className="font-display text-lg font-semibold">
            Budget status — {MONTHS[month - 1]} {year}
          </h2>
          {q.isPending ? (
            <div className="space-y-3" role="status" aria-label="Loading budgets">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full rounded-2xl" />
              ))}
            </div>
          ) : q.isError ? (
            <ErrorState error={q.error} title="Couldn't load budgets" onRetry={() => void q.refetch()} />
          ) : q.data.items.length === 0 ? (
            <EmptyState
              icon={<Wallet />}
              title="No budgets set for this month"
              description="Pick a category and an amount on the left. Spending is tracked against it automatically."
            />
          ) : (
            <Stagger className="space-y-3">
              {q.data.items.map((b) => {
                const tone = meterTone(b.percent_used);
                return (
                  <StaggerItem key={b.id}>
                    <Card className="p-4 sm:p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h3 className="font-display text-base font-semibold">{b.category}</h3>
                          <p className="text-sm text-muted-foreground tabular-nums">
                            {money(b.actual_spent)} of {money(b.budget_amount)} ({Math.round(b.percent_used)}% used)
                          </p>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge tone={tone === "danger" ? "danger" : tone === "warning" ? "warning" : tone === "info" ? "info" : "success"}>
                            {tone === "danger" ? "Over budget" : tone === "warning" ? "Almost at limit" : tone === "info" ? "Getting close" : "On track"}
                          </Badge>
                          <IconButton label={`Delete ${b.category} budget`} size="icon-sm" onClick={() => setDeleting(b)}>
                            <Trash2 className="text-danger" />
                          </IconButton>
                        </div>
                      </div>
                      <Meter className="mt-3" value={b.percent_used} tone={tone} label={`${b.category} budget used`} />
                      <p className={cn("mt-2 text-xs", tone === "danger" ? "text-danger" : "text-muted-foreground")}>
                        {b.percent_used >= 100 ? `Exceeded by ${money(Math.abs(b.remaining))}.` : `${money(b.remaining)} remaining.`}
                      </p>
                    </Card>
                  </StaggerItem>
                );
              })}
            </Stagger>
          )}
        </section>
      </div>

      {deleting && (
        <ConfirmModal
          open
          onOpenChange={(o) => !o && setDeleting(null)}
          title={`Delete the ${deleting.category} budget?`}
          description="Your transactions stay; only the limit for this month is removed."
          onConfirm={async () => {
            await remove.mutateAsync(deleting.id);
            setDeleting(null);
          }}
        />
      )}
    </>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarCheck, LineChart as LineIcon, RefreshCw, Scale, Target, Trash2, TrendingDown } from "lucide-react";
import { useState, type FormEvent } from "react";
import { CartesianGrid, ComposedChart, Bar, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";

import { ChartCard, ChartTooltip, axisProps, gridProps, SERIES } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard, Timeline } from "@/components/ui/Display";
import { ConfirmModal } from "@/components/ui/Overlay";
import { EmptyState, ErrorState, InlineLoader, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import api, { errorMessage, today } from "@/lib/api";
import { fmt } from "@/lib/evaluation";
import { keys } from "@/lib/queries";
import type { ProgressResponse, Recalculation, Weight, WeightSaveResponse } from "@/lib/types";

const RANGES = [
  { value: "14", label: "Last 14 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
];

const shortDate = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
const longDate = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

export default function Progress() {
  const qc = useQueryClient();
  const [days, setDays] = useState(30);
  const [date, setDate] = useState(today());
  const [weight, setWeight] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [recalc, setRecalc] = useState<Recalculation | null>(null);

  const progress = useQuery({
    queryKey: keys.progress(days),
    queryFn: async () => (await api.get<ProgressResponse>("/progress", { params: { days } })).data,
  });

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ["progress"] });
    qc.invalidateQueries({ queryKey: keys.targets });
  };

  const saveWeight = useMutation({
    mutationFn: async (body: { date: string; weight_kg: number }) => (await api.post<WeightSaveResponse>("/weights", body)).data,
    onSuccess: (r) => {
      refreshAll();
      setWeight("");
      setFormError(null);
      if (r.recalculated) {
        setRecalc(r.recalculated);
        toast.success(`Weight saved. Target updated to ${fmt(r.target_kcal)} kcal.`);
      } else {
        toast.success("Weight saved.");
      }
    },
    onError: (err) => setFormError(errorMessage(err)),
  });

  const removeWeight = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/weights/${id}`)).data,
    onSuccess: () => {
      refreshAll();
      toast.success("Weight entry removed.");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const recalcNow = useMutation({
    mutationFn: async () => (await api.post<Recalculation>("/progress/recalculate")).data,
    onSuccess: (r) => {
      refreshAll();
      setRecalc(r);
      setFormError(null);
      toast.success(`Target recalculated: ${fmt(r.old_target_kcal)} → ${fmt(r.new_target_kcal)} kcal.`);
    },
    onError: (err) => setFormError(errorMessage(err)),
  });

  function submitWeight(e: FormEvent) {
    e.preventDefault();
    const kg = Number(weight);
    if (!weight || Number.isNaN(kg) || kg < 30 || kg > 250) {
      setFormError("Weight must be between 30 and 250 kg.");
      return;
    }
    if (date > today()) {
      setFormError("Weight date cannot be in the future.");
      return;
    }
    setFormError(null);
    saveWeight.mutate({ date, weight_kg: kg });
  }

  if (progress.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Progress" description="Loading your weight and intake." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (progress.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Progress" />
        <ErrorState error={progress.error} title="Couldn't load your progress" onRetry={() => progress.refetch()} />
      </div>
    );
  }

  const p = progress.data;
  const windowStart = p.intake[0]?.date ?? "";
  const weights = p.weights.filter((w) => w.date >= windowStart);
  const hasWeights = weights.length > 0;
  const hasIntake = p.intake.some((d) => d.kcal > 0);

  const weightRows = weights.map((w) => ({ date: shortDate(w.date), kg: w.weight_kg }));
  const intakeRows = p.intake.map((d) => ({ day: shortDate(d.date), eaten: Math.round(d.kcal), target: Math.round(d.target) }));

  const historyColumns: Column<Weight>[] = [
    { key: "date", header: "Date", cell: (w) => longDate(w.date), sortValue: (w) => w.date, align: "left" },
    { key: "kg", header: "Weight", cell: (w) => `${w.weight_kg.toFixed(1)} kg`, sortValue: (w) => w.weight_kg, align: "right" },
    {
      key: "actions",
      header: <span className="sr-only">Actions</span>,
      align: "right",
      cell: (w) => (
        <ConfirmModal
          title={`Delete the ${w.weight_kg.toFixed(1)} kg entry from ${longDate(w.date)}?`}
          description="Trend and adherence will be recalculated without it."
          confirmLabel="Delete"
          onConfirm={() => removeWeight.mutateAsync(w.id)}
          trigger={
            <Button variant="ghost" size="icon-sm" aria-label={`Delete weight from ${longDate(w.date)}`} className="text-muted-foreground hover:text-danger">
              <Trash2 />
            </Button>
          }
        />
      ),
    },
  ];

  const sortedWeights = [...p.weights].sort((a, b) => b.date.localeCompare(a.date));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Progress"
        description="Log your weight and see how intake and trend line up with your target."
        actions={
          <div className="w-44">
            <Select value={String(days)} onValueChange={(v) => setDays(Number(v))} options={RANGES} aria-label="Range" />
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Adherence (7 days)"
          value={p.adherence.score}
          format={(n) => `${Math.round(n)}/100`}
          hint={`${p.adherence.days_logged} of ${p.adherence.window_days} days logged`}
          icon={<CalendarCheck />}
        />
        <StatCard label="Current target" value={p.current_target} format={(n) => `${fmt(n)} kcal`} hint="Recalculated from your trend" icon={<Target />} accent="cyan" />
        <StatCard
          label="Weight trend"
          display={p.trend_kg_week === null ? "Not enough data" : `${p.trend_kg_week > 0 ? "+" : ""}${p.trend_kg_week.toFixed(2)} kg/wk`}
          hint={p.trend_kg_week === null ? "Log 3+ weights across 7 days" : "Over the last 2 weeks"}
          icon={<TrendingDown />}
          accent="magenta"
        />
        <StatCard
          label="Goal rate"
          display={`${p.goal_rate_kg_week > 0 ? "+" : ""}${p.goal_rate_kg_week.toFixed(2)} kg/wk`}
          hint="What your goal asks for"
          icon={<LineIcon />}
        />
      </div>

      {recalc && (
        <div role="status" className="glass flex flex-col gap-2 rounded-2xl border border-success/30 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-0.5">
            <p className="font-medium">Your target was recalculated</p>
            <p className="text-sm text-muted-foreground">{recalc.reason}</p>
          </div>
          <Badge tone="success" className="self-start text-sm sm:self-center">
            {fmt(recalc.old_target_kcal)} → {fmt(recalc.new_target_kcal)} kcal
          </Badge>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard
          title="Weight"
          description={hasWeights ? `${weights.length} reading${weights.length === 1 ? "" : "s"} in this range` : undefined}
          legend={[{ label: "Weight (kg)", color: SERIES[0] }]}
          table={{ columns: ["Day", "Weight (kg)"], rows: weightRows.map((r) => [r.date, r.kg]) }}
          empty={hasWeights ? undefined : "No weights in this range yet. Log today's weight below."}
        >
          <div className="h-64 w-full" role="img" aria-label="Line chart of your weight over the selected range">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weightRows} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="date" {...axisProps} minTickGap={16} />
                <YAxis {...axisProps} domain={["dataMin - 1", "dataMax + 1"]} width={44} />
                <Tooltip content={<ChartTooltip formatter={(v) => `${Number(v).toFixed(1)} kg`} />} />
                <Line type="monotone" dataKey="kg" name="Weight" stroke={SERIES[0]} strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard
          title="Calories eaten vs target"
          description="Bars are logged calories per day; the line is your target that day."
          legend={[
            { label: "Eaten", color: SERIES[0] },
            { label: "Target", color: SERIES[1] },
          ]}
          table={{ columns: ["Day", "Eaten (kcal)", "Target (kcal)"], rows: intakeRows.map((r) => [r.day, r.eaten, r.target]) }}
          empty={hasIntake ? undefined : "Nothing logged in this range yet. Calories appear here once you log food."}
        >
          <div className="h-64 w-full" role="img" aria-label="Bar chart of calories eaten against target for the selected range">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={intakeRows} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="day" {...axisProps} minTickGap={16} />
                <YAxis {...axisProps} width={48} />
                <Tooltip content={<ChartTooltip formatter={(v) => `${fmt(Number(v))} kcal`} />} cursor={{ fill: "var(--muted)" }} />
                <Bar dataKey="eaten" name="Eaten" fill={SERIES[0]} radius={[6, 6, 0, 0]} maxBarSize={20} />
                <Line dataKey="target" name="Target" stroke={SERIES[1]} strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Log weight" description="One reading per day. Logging again replaces that day's value." icon={<Scale />} />
          <CardBody>
            <form className="space-y-4" onSubmit={submitWeight} noValidate>
              <FormField label="Date" hint="Today or an earlier day">
                {(f) => <Input {...f} type="date" max={today()} value={date} onChange={(e) => setDate(e.target.value)} />}
              </FormField>
              <FormField label="Weight (kg)" hint="30 to 250">
                {(f) => (
                  <Input
                    {...f}
                    type="number"
                    inputMode="decimal"
                    step="0.1"
                    min={30}
                    max={250}
                    placeholder="e.g. 65.8"
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                  />
                )}
              </FormField>
              {formError && (
                <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] px-3 py-2 text-sm text-danger">
                  {formError}
                </p>
              )}
              <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
                <Button type="submit" loading={saveWeight.isPending} className="flex-1">
                  Save weight
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  className="flex-1"
                  loading={recalcNow.isPending}
                  onClick={() => recalcNow.mutate()}
                  title="Recalculate from the weights you have logged"
                >
                  <RefreshCw /> Recalculate target now
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                The target recalculates automatically once readings cover a week. Recalculate now uses the readings you have.
              </p>
            </form>
          </CardBody>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Weight history" description={`${p.weights.length} entr${p.weights.length === 1 ? "y" : "ies"} in total`} />
          <CardBody>
            {saveWeight.isPending && <InlineLoader label="Saving your weight" className="mb-3" />}
            <Table<Weight>
              caption="Your logged weights, newest first"
              columns={historyColumns}
              rows={sortedWeights}
              rowKey={(w) => w.id}
              pageSize={8}
              initialSort={{ key: "date", dir: "desc" }}
              empty={
                <EmptyState icon={<Scale />} title="No weights logged yet" description="Log your weight to start the trend and see the target update." />
              }
            />
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="How your target is set" description="Each change is recorded here with the reason" />
        <CardBody>
          {p.target_history.length === 0 ? (
            <EmptyState icon={<Target />} title="No target history yet" description="Save your profile to create the first target." />
          ) : (
            <Timeline
              items={[...p.target_history].reverse().map((h) => ({
                icon: <Target />,
                title: `${fmt(h.kcal)} kcal a day`,
                meta: `${longDate(h.date)} · at ${h.weight_kg.toFixed(1)} kg`,
                body: h.reason,
              }))}
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

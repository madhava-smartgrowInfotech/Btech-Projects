import { useQuery } from "@tanstack/react-query";
import { Activity, Flame, NotebookPen, Target } from "lucide-react";
import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router";

import { ChartCard, ChartTooltip, axisProps, gridProps, SERIES } from "@/components/charts/Chart";
import { PageHeader } from "@/components/ui/Layout";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { CardsSkeleton, EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { StatCard } from "@/components/ui/Display";
import { Badge } from "@/components/ui/Badge";
import api, { today } from "@/lib/api";
import { fmt } from "@/lib/evaluation";
import { keys } from "@/lib/queries";
import { MEALS, type LogDay, type Plan, type PlanLatestResponse, type ProgressResponse, type Targets } from "@/lib/types";

const longDate = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });
const shortDay = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { weekday: "short", day: "numeric" });

export default function Dashboard() {
  const date = today();
  const targets = useQuery({
    queryKey: keys.targets,
    queryFn: async () => (await api.get<Targets>("/targets")).data,
  });
  const logs = useQuery({
    queryKey: keys.logs(date),
    queryFn: async () => (await api.get<LogDay>("/logs", { params: { date } })).data,
  });
  const plan = useQuery({
    queryKey: keys.plan,
    queryFn: async () => (await api.get<PlanLatestResponse>("/plans/latest")).data,
  });
  const progress = useQuery({
    queryKey: keys.progress(7),
    queryFn: async () => (await api.get<ProgressResponse>("/progress", { params: { days: 7 } })).data,
  });

  const retryAll = () => {
    targets.refetch();
    logs.refetch();
    plan.refetch();
    progress.refetch();
  };

  if (targets.isPending || logs.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Today" description={longDate(date)} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
        <CardsSkeleton count={2} />
      </div>
    );
  }

  if (targets.isError || logs.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Today" description={longDate(date)} />
        <ErrorState error={targets.error ?? logs.error} title="Couldn't load today's numbers" onRetry={retryAll} />
      </div>
    );
  }

  const t = targets.data;
  const day = logs.data;
  const todayPlan: Plan["days"][number] | undefined = plan.data?.plan?.days.find((d) => d.date === date);
  const kcalTarget = t.kcal;
  const pctKcal = kcalTarget ? (day.totals.kcal / kcalTarget) * 100 : 0;

  const chartRows = (progress.data?.intake ?? []).map((d) => ({
    day: shortDay(d.date),
    eaten: Math.round(d.kcal),
    target: Math.round(d.target),
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={longDate(date)}
        title="Today"
        description={`Your target is ${fmt(kcalTarget)} kcal. ${Math.round(day.totals.kcal) > 0 ? `You've logged ${fmt(day.totals.kcal)} so far.` : "Nothing logged yet today."}`}
        actions={
          <>
            <Button asChild variant="secondary">
              <Link to="/log">
                <NotebookPen /> Log food
              </Link>
            </Button>
            <Button asChild>
              <Link to="/plan">
                <Target /> Weekly plan
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Calories eaten"
          value={day.totals.kcal}
          format={fmt}
          hint={`of ${fmt(kcalTarget)} kcal · ${Math.round(pctKcal)}%`}
          icon={<Flame />}
          accent="magenta"
        />
        <StatCard label="Protein" value={day.totals.protein} format={(n) => `${fmt(n)} g`} hint={`of ${fmt(day.targets.protein)} g`} icon={<Activity />} accent="cyan" />
        <StatCard label="Carbs" value={day.totals.carbs} format={(n) => `${fmt(n)} g`} hint={`of ${fmt(day.targets.carbs)} g`} icon={<Activity />} />
        <StatCard
          label="Adherence (7 days)"
          value={progress.data?.adherence.score ?? null}
          format={(n) => `${Math.round(n)}/100`}
          display={progress.isError ? "-" : undefined}
          hint={progress.data ? `${progress.data.adherence.days_logged} of ${progress.data.adherence.window_days} days logged` : "Loading…"}
          icon={<Target />}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {progress.isPending ? (
            <Skeleton className="h-80 rounded-2xl" />
          ) : progress.isError ? (
            <ErrorState error={progress.error} title="Couldn't load the last 7 days" onRetry={() => progress.refetch()} />
          ) : (
            <ChartCard
              title="Last 7 days: calories vs target"
              description="Bars are what you logged; the line is your target that day."
              legend={[
                { label: "Eaten", color: SERIES[0] },
                { label: "Target", color: SERIES[1] },
              ]}
              table={{
                columns: ["Day", "Eaten (kcal)", "Target (kcal)"],
                rows: chartRows.map((r) => [r.day, r.eaten, r.target]),
              }}
              empty={chartRows.every((r) => r.eaten === 0) ? "Log a meal and this chart fills in." : undefined}
            >
              <div className="h-64 w-full" role="img" aria-label="Bar chart of calories eaten against target for the last 7 days">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartRows} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="day" {...axisProps} />
                    <YAxis {...axisProps} width={48} />
                    <Tooltip content={<ChartTooltip formatter={(v) => `${fmt(Number(v))} kcal`} />} cursor={{ fill: "var(--muted)" }} />
                    <Bar dataKey="eaten" name="Eaten" fill={SERIES[0]} radius={[8, 8, 0, 0]} maxBarSize={36} />
                    <Line dataKey="target" name="Target" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </ChartCard>
          )}
        </div>

        <Card>
          <CardHeader title="Today's targets" description={`${t.bmi_category} · BMI ${t.bmi}`} />
          <CardBody className="space-y-4">
            <Macro label="Calories" value={day.totals.kcal} target={kcalTarget} unit="kcal" />
            <Macro label="Protein" value={day.totals.protein} target={day.targets.protein} unit="g" />
            <Macro label="Carbs" value={day.totals.carbs} target={day.targets.carbs} unit="g" />
            <Macro label="Fat" value={day.totals.fat} target={day.targets.fat} unit="g" />
            <Macro label="Fibre" value={day.totals.fibre} target={day.targets.fibre} unit="g" />
            <ul className="space-y-1 pt-2 text-xs text-muted-foreground">
              {t.notes.map((n) => (
                <li key={n}>• {n}</li>
              ))}
            </ul>
            <p className="text-xs text-muted-foreground">{t.disclaimer}</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Logged today"
            description={day.entries.length ? `${day.entries.length} item${day.entries.length === 1 ? "" : "s"}` : undefined}
            action={
              <Button asChild variant="ghost" size="sm">
                <Link to="/log">Open food log</Link>
              </Button>
            }
          />
          <CardBody>
            {day.entries.length === 0 ? (
              <EmptyState
                icon={<NotebookPen />}
                title="Nothing logged yet"
                description="Search a dish, look up an ingredient, or photograph your plate."
                action={
                  <Button asChild size="sm">
                    <Link to="/log">Log food</Link>
                  </Button>
                }
                className="py-8"
              />
            ) : (
              <div className="space-y-5">
                {MEALS.map((m) => {
                  const items = day.entries.filter((e) => e.meal === m.value);
                  if (!items.length) return null;
                  return (
                    <section key={m.value} aria-labelledby={`dash-${m.value}`}>
                      <h3 id={`dash-${m.value}`} className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        {m.label}
                      </h3>
                      <ul className="divide-y divide-[var(--glass-border)]">
                        {items.map((e) => (
                          <li key={e.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                            <span className="min-w-0 truncate">
                              {e.name} <span className="text-muted-foreground">· {Math.round(e.grams)} g</span>
                            </span>
                            <span className="shrink-0 tabular-nums">{fmt(e.kcal)} kcal</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  );
                })}
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="Today's plan"
            description={todayPlan ? `Day ${todayPlan.day} of your week` : undefined}
            action={
              <Button asChild variant="ghost" size="sm">
                <Link to="/plan">Open plan</Link>
              </Button>
            }
          />
          <CardBody>
            {plan.isPending ? (
              <CardsSkeleton count={1} className="lg:grid-cols-1" />
            ) : plan.isError ? (
              <ErrorState error={plan.error} title="Couldn't load your plan" onRetry={() => plan.refetch()} />
            ) : !plan.data?.plan ? (
              <EmptyState
                icon={<Target />}
                title="No plan yet"
                description="Generate a 7-day plan sized to your target and allergies."
                action={
                  <Button asChild size="sm">
                    <Link to="/plan">Generate my weekly plan</Link>
                  </Button>
                }
                className="py-8"
              />
            ) : !todayPlan ? (
              <EmptyState
                icon={<Target />}
                title="Today isn't in your plan"
                description={`Your plan covers ${longDate(plan.data.plan.start_date)} onward. Generate a new week to cover today.`}
                action={
                  <Button asChild size="sm" variant="secondary">
                    <Link to="/plan">Open weekly plan</Link>
                  </Button>
                }
                className="py-8"
              />
            ) : (
              <div className="space-y-4">
                {MEALS.map((m) => {
                  const dishes = todayPlan.meals[m.value];
                  const kcal = dishes.reduce((s, d) => s + d.kcal, 0);
                  return (
                    <div key={m.value} className="flex items-start justify-between gap-3 text-sm">
                      <div className="min-w-0">
                        <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{m.label}</div>
                        <div className="truncate">{dishes.map((d) => d.name).join(" + ") || "-"}</div>
                      </div>
                      <Badge tone="neutral" className="shrink-0 tabular-nums">
                        {fmt(kcal)} kcal
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function Macro({ label, value, target, unit }: { label: string; value: number; target: number; unit: string }) {
  const pct = target ? (value / target) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="tabular-nums text-muted-foreground">
          {fmt(value)} / {fmt(target)} {unit}
        </span>
      </div>
      <ProgressBar value={pct} label={`${label}: ${Math.round(pct)} percent of target`} />
    </div>
  );
}

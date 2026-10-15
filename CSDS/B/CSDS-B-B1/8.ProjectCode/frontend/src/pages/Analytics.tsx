import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Area, AreaChart, ResponsiveContainer, Tooltip as RTooltip, XAxis } from "recharts";
import { Brain, CircleAlert, Clock, Flame, Gauge, Inbox, Map as MapIcon, Pencil, RefreshCw, Target, Timer, TrendingUp } from "lucide-react";
import { lazy, Suspense, useMemo, useState } from "react";
import { Link } from "react-router";

import { PRIORITY_COLOR } from "@/components/domain/Badges";
import { RetrainPanel } from "@/components/domain/RetrainPanel";
import { ChartGradients, ChartCard, ChartTooltip, SERIES } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { Input, Label } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { Segmented } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { days, pct } from "@/lib/format";
import { keys, useHotspots, useMeta, useModelInfo, useSla, useSummary, useTrends } from "@/lib/queries";
import type { ModelMetrics, SlaRow, Trends } from "@/lib/types";

const HotspotMap = lazy(() => import("@/components/map/HotspotMap"));
const HEAT = ["#67E8F9", "#38BDF8", "#7C8CFF", "#7C5CFF", "#C45CF2", "#F472B6"];
const ALL = "__all__";

/* ---------- hotspot map + recurring issues ---------- */

function Hotspots() {
  const meta = useMeta();
  const [win, setWin] = useState(30);
  const [category, setCategory] = useState(ALL);
  const [points, setPoints] = useState(false);
  const q = useHotspots(win, category === ALL ? "" : category);
  const data = q.data;

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <Card>
        <CardHeader title="Hotspot map" description="Where complaints are concentrating." icon={<MapIcon />} />
        <CardBody className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Select
              className="w-40"
              aria-label="Time window"
              value={String(win)}
              onValueChange={(v) => setWin(Number(v))}
              options={[7, 30, 90].map((d) => ({ value: String(d), label: `Last ${d} days` }))}
            />
            <Select
              className="w-52"
              aria-label="Category"
              value={category}
              onValueChange={setCategory}
              options={[{ value: ALL, label: "All categories" }, ...(meta.data?.categories.map((c) => ({ value: c.name, label: c.name })) ?? [])]}
            />
            <Segmented
              label="Map mode"
              size="sm"
              value={points ? "points" : "wards"}
              onChange={(v) => setPoints(v === "points")}
              options={[
                { value: "wards", label: "Wards" },
                { value: "points", label: "Complaints" },
              ]}
            />
          </div>
          <div className="h-[420px] overflow-hidden rounded-2xl border border-[var(--glass-border)]">
            {q.isPending ? (
              <Skeleton className="h-full w-full rounded-none" />
            ) : q.isError && !data ? (
              <ErrorState error={q.error} title="Couldn't load the map" onRetry={() => q.refetch()} className="h-full justify-center border-0" />
            ) : data && data.wards.length === 0 && data.points.length === 0 ? (
              <EmptyState icon={<MapIcon />} title="No located complaints in this window" description="Try a longer time window or all categories." className="h-full border-0" />
            ) : data ? (
              <Suspense fallback={<Skeleton className="h-full w-full rounded-none" />}>
                <HotspotMap data={data} showPoints={points} />
              </Suspense>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            {points ? (
              (Object.entries(PRIORITY_COLOR) as [string, string][]).map(([p, color]) => (
                <span key={p} className="inline-flex items-center gap-1.5">
                  <span className="size-2.5 rounded-full" style={{ background: color }} /> {p}
                </span>
              ))
            ) : (
              <span className="inline-flex items-center gap-1.5">
                Fewer
                {HEAT.map((c) => (
                  <span key={c} className="h-2.5 w-4 rounded-sm" style={{ background: c }} />
                ))}
                More complaints (circle size and shade)
              </span>
            )}
            {data && <span className="ml-auto">{data.points.length} located complaints in window</span>}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Recurring issues" description={`Same category reported 3+ times in one ward in the last ${win} days.`} icon={<Flame />} />
        <CardBody>
          {q.isPending ? (
            <div className="space-y-2" role="status" aria-label="Loading recurring issues">
              {[0, 1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : data && data.recurring.length ? (
            <Table
              caption="Recurring issues by ward"
              rows={data.recurring}
              rowKey={(r) => r.ward + r.category}
              pageSize={8}
              initialSort={{ key: "count", dir: "desc" }}
              columns={[
                { key: "ward", header: "Ward", cell: (r) => r.ward, sortValue: (r) => r.ward },
                { key: "category", header: "Issue", cell: (r) => <span className="text-muted-foreground">{r.category}</span>, sortValue: (r) => r.category },
                { key: "count", header: "Reports", align: "right", cell: (r) => <b>{r.count}</b>, sortValue: (r) => r.count },
                { key: "open", header: "Open", align: "right", cell: (r) => r.open, sortValue: (r) => r.open },
              ]}
            />
          ) : (
            <EmptyState icon={<Flame />} title="No recurring issues" description="Nothing was reported 3+ times in one ward in this window." className="py-8" />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

/* ---------- SLA table with admin editing ---------- */

function SlaSection() {
  const { user } = useAuth();
  const qc = useQueryClient();
  const sla = useSla();
  const meta = useMeta();
  const isAdmin = user?.role === "admin";
  const [edit, setEdit] = useState<{ row: SlaRow; value: string } | null>(null);
  const [error, setError] = useState("");

  const save = useMutation({
    mutationFn: async () => {
      const d = meta.data?.departments.find((x) => x.name === edit!.row.department);
      if (!d) throw new Error("Department list is still loading - try again in a moment.");
      return (await api.put(`/departments/${d.id}`, { sla_days: Number(edit!.value) })).data;
    },
    onMutate: () => setError(""),
    onSuccess: () => {
      toast.success(`${edit!.row.department}: SLA is now ${edit!.value} days`);
      setEdit(null);
      qc.invalidateQueries({ queryKey: keys.sla });
      qc.invalidateQueries({ queryKey: keys.meta });
      qc.invalidateQueries({ queryKey: ["analytics"] });
      qc.invalidateQueries({ queryKey: ["queue"] });
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const columns: Column<SlaRow>[] = [
    { key: "department", header: "Department", cell: (r) => <span className="font-medium">{r.department}</span>, sortValue: (r) => r.department },
    {
      key: "sla",
      header: "SLA",
      sortValue: (r) => r.sla_days,
      cell: (r) => (
        <span className="inline-flex items-center gap-1.5">
          {r.sla_days} d
          {isAdmin && (
            <Button variant="ghost" size="icon-sm" magnetic={false} aria-label={`Edit the SLA for ${r.department}`} onClick={() => setEdit({ row: r, value: String(r.sla_days) })}>
              <Pencil />
            </Button>
          )}
        </span>
      ),
    },
    {
      key: "compliance",
      header: "Resolved within SLA",
      className: "min-w-44",
      sortValue: (r) => r.compliance,
      cell: (r) =>
        r.compliance === null ? (
          <span className="text-muted-foreground">No resolved complaints yet</span>
        ) : (
          <div className="flex items-center gap-2" title={`${r.within_sla} of ${r.resolved} resolved within ${r.sla_days} days`}>
            <ProgressBar value={r.compliance * 100} label={`${r.department}: resolved within SLA`} className="flex-1" />
            <span className="w-12 text-right text-xs tabular-nums">{Math.round(r.compliance * 100)}%</span>
          </div>
        ),
    },
    { key: "resolved", header: "Resolved", align: "right", cell: (r) => r.resolved, sortValue: (r) => r.resolved },
    { key: "avg", header: "Avg days", align: "right", cell: (r) => r.avg_days ?? "-", sortValue: (r) => r.avg_days },
    { key: "open", header: "Open", align: "right", cell: (r) => r.open, sortValue: (r) => r.open },
    { key: "breached", header: "Open past SLA", align: "right", cell: (r) => <b>{r.open_breached}</b>, sortValue: (r) => r.open_breached },
  ];

  return (
    <Card>
      <CardHeader title="SLA compliance by department" description={isAdmin ? "Pencil icons edit a department's SLA." : "Administrators can edit SLA days."} icon={<Timer />} />
      <CardBody>
        {sla.isPending ? (
          <div className="space-y-2" role="status" aria-label="Loading SLA compliance">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : sla.isError ? (
          <ErrorState error={sla.error} title="Couldn't load SLA compliance" onRetry={() => sla.refetch()} />
        ) : (
          <Table caption="SLA compliance by department" columns={columns} rows={sla.data} rowKey={(r) => r.department} pageSize={10} />
        )}
      </CardBody>

      <Modal
        open={!!edit}
        onOpenChange={(o) => !o && !save.isPending && setEdit(null)}
        title={`SLA for ${edit?.row.department ?? ""}`}
        description="How many days the department has to resolve a complaint (1-90)."
        footer={
          <>
            <Button variant="secondary" magnetic={false} onClick={() => setEdit(null)} disabled={save.isPending}>
              Cancel
            </Button>
            <Button onClick={() => save.mutate()} loading={save.isPending}>
              Save SLA
            </Button>
          </>
        }
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
          className="space-y-2"
        >
          <Label htmlFor="sla-days">SLA in days</Label>
          <Input id="sla-days" type="number" min={1} max={90} value={edit?.value ?? ""} onChange={(e) => edit && setEdit({ ...edit, value: e.target.value })} autoFocus />
          {error && (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          )}
        </form>
      </Modal>
    </Card>
  );
}

/* ---------- weekly trends ---------- */

function TrendTile({ title, weeks, counts, color }: { title: string; weeks: string[]; counts: number[]; color: string }) {
  const data = useMemo(() => weeks.map((w, i) => ({ week: w, count: counts[i] })), [weeks, counts]);
  const total = counts.reduce((a, b) => a + b, 0);
  const gid = `trend-${title.replace(/\W/g, "")}`;
  return (
    <div className="glass-flat rounded-xl p-3">
      <div className="flex items-baseline justify-between gap-2">
        <div className="truncate text-xs font-semibold" title={title}>
          {title}
        </div>
        <div className="text-xs tabular-nums text-muted-foreground">{total} total</div>
      </div>
      <div className="mt-1 h-16" role="img" aria-label={`${title}: complaints per week, ${counts.join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
            <defs>
              <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="week" hide />
            <RTooltip
              cursor={{ stroke: "var(--chart-axis)", strokeDasharray: "3 3" }}
              content={<ChartTooltip labelFormatter={(l) => `7 days from ${new Date(String(l)).toLocaleDateString(undefined, { day: "numeric", month: "short" })}`} />}
            />
            <Area type="monotone" dataKey="count" name="Complaints" stroke={color} strokeWidth={2} fill={`url(#${gid})`} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function TrendsSection({ data }: { data: Trends }) {
  const top = data.series.slice(0, 8);
  const rest = data.series.slice(8);
  const other = rest.length ? [{ category: `Other (${rest.length} categories)`, counts: data.weeks.map((_, i) => rest.reduce((a, s) => a + s.counts[i], 0)) }] : [];
  const all = [...top, ...other];
  const label = (w: string) => new Date(w).toLocaleDateString(undefined, { day: "numeric", month: "short" });
  return (
    <ChartCard
      title="Category trends"
      description="Complaints per 7 days, last 12 weeks."
      icon={<TrendingUp />}
      empty={data.series.length === 0 ? "No complaints in the last 12 weeks." : undefined}
      table={{ columns: ["Category", ...data.weeks.map(label)], rows: data.series.map((s) => [s.category, ...s.counts]) }}
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {all.map((s, i) => (
          <TrendTile key={s.category} title={s.category} weeks={data.weeks} counts={s.counts} color={SERIES[i % 3]} />
        ))}
      </div>
    </ChartCard>
  );
}

/* ---------- model performance ---------- */

function ModelCard({ m }: { m: ModelMetrics }) {
  const rows = [
    { task: "Category", v: m.category },
    { task: "Department", v: m.department },
    { task: "Priority", v: m.priority },
  ];
  const r = m.resolution;
  return (
    <Card>
      <CardHeader title={`Model performance on held-out data (v${m.version})`} description="Complaints the model never saw while training." icon={<Brain />} />
      <CardBody className="space-y-3">
        <Table
          caption="Held-out accuracy by task and language"
          rows={rows}
          rowKey={(r) => r.task}
          columns={[
            { key: "task", header: "Task", cell: (r) => r.task },
            { key: "acc", header: "Accuracy", align: "right", cell: (r) => <b>{pct(r.v.test.accuracy)}</b> },
            { key: "f1", header: "Macro-F1", align: "right", cell: (r) => r.v.test.macro_f1.toFixed(3) },
            { key: "en", header: "English", align: "right", cell: (r) => pct(r.v.by_language.English) },
            { key: "hi", header: "Hindi", align: "right", cell: (r) => pct(r.v.by_language.Hindi) },
            { key: "hg", header: "Hinglish", align: "right", cell: (r) => pct(r.v.by_language.Hinglish) },
          ]}
        />
        {r && (
          <p className="text-xs leading-relaxed text-muted-foreground">
            <b className="text-foreground">Resolution time</b> (NYC 311, {r.rows_test.toLocaleString()} held-out requests): typical error {r.median_abs_error_days} days vs{" "}
            {r.baseline_category_median_median_abs_error_days ?? "-"} for a per-category median; mean error {r.mae_days} vs {r.baseline_category_median_mae_days ?? "-"} days; SLA-breach flag correct{" "}
            {pct(r.sla_breach_flag_accuracy)}.
          </p>
        )}
      </CardBody>
    </Card>
  );
}

function ModelSection() {
  const info = useModelInfo();
  if (info.isPending) return <Skeleton className="h-64 w-full rounded-2xl" />;
  if (info.isError) return <ErrorState error={info.error} title="Couldn't load model performance" onRetry={() => info.refetch()} />;
  if (!info.data.current) return <EmptyState icon={<Brain />} title="No evaluation yet" description="Train the models (python ml/train.py) to see their held-out metrics here." />;
  return <ModelCard m={info.data.current} />;
}

/* ---------- page ---------- */

export default function Analytics() {
  const summary = useSummary();
  const trends = useTrends();
  const s = summary.data;
  const acc = s?.ai_acceptance.department;

  return (
    <div className="space-y-5">
      <PageHeader
        title="Hotspots & analytics"
        description={
          s
            ? `Live from every complaint in the system · refreshes every 20 seconds · updated ${new Date(s.updated_at).toLocaleTimeString()}`
            : "Live from every complaint in the system · refreshes every 20 seconds"
        }
        actions={
          <Button variant="secondary" magnetic={false} loading={summary.isFetching} onClick={() => summary.refetch()}>
            {!summary.isFetching && <RefreshCw />} Refresh
          </Button>
        }
      />

      {summary.isPending ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4" role="status" aria-label="Loading key figures">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-[132px] rounded-2xl" />
          ))}
        </div>
      ) : summary.isError ? (
        <ErrorState error={summary.error} title="Couldn't load the key figures" hint="Everything below keeps refreshing on its own." onRetry={() => summary.refetch()} />
      ) : s && s.total === 0 ? (
        <EmptyState icon={<Inbox />} title="No complaints yet" description="Figures, hotspots and trends appear as soon as citizens start filing complaints." />
      ) : s ? (
        <Stagger className="grid grid-cols-2 gap-3 md:grid-cols-4" gap={0.05}>
          <StaggerItem>
            <StatCard label="Open complaints" value={s.open} hint={`${s.filed_last_24h} filed in 24 h`} icon={<Inbox />} className="h-full" />
          </StaggerItem>
          <StaggerItem>
            <Link to="/app/queue" className="block h-full rounded-2xl" aria-label={`Awaiting review: ${s.awaiting_review}. Open the triage queue`}>
              <StatCard label="Awaiting review" value={s.awaiting_review} hint="Open the triage queue" icon={<Clock />} accent="cyan" className="h-full" />
            </Link>
          </StaggerItem>
          <StaggerItem>
            <StatCard label="Resolved within SLA" display={pct(s.sla_compliance)} hint="All resolved complaints" icon={<Target />} accent="cyan" className="h-full" />
          </StaggerItem>
          <StaggerItem>
            <StatCard label="Open past SLA" value={s.open_sla_breached} hint="Need escalation" icon={<CircleAlert />} accent="magenta" className="h-full" />
          </StaggerItem>
          <StaggerItem>
            <StatCard label="Avg resolution" display={days(s.avg_resolution_days)} hint={`${s.resolved_last_30d} resolved in 30 d`} icon={<Timer />} className="h-full" />
          </StaggerItem>
          <StaggerItem>
            <StatCard label="AI department accepted" display={pct(acc?.rate)} hint={`${acc?.accepted ?? 0} of ${acc?.reviewed ?? 0} officer reviews`} icon={<Brain />} accent="magenta" className="h-full" />
          </StaggerItem>
          <StaggerItem>
            <StatCard label="Time estimate error" display={days(s.time_estimate_mae_days)} hint="Mean, on resolved complaints" icon={<Gauge />} accent="cyan" className="h-full" />
          </StaggerItem>
        </Stagger>
      ) : null}

      <Hotspots />
      <SlaSection />

      {trends.isPending ? (
        <Skeleton className="h-64 w-full rounded-2xl" />
      ) : trends.isError ? (
        <ErrorState error={trends.error} title="Couldn't load category trends" onRetry={() => trends.refetch()} />
      ) : (
        <TrendsSection data={trends.data} />
      )}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <ModelSection />
        <RetrainPanel />
      </div>
    </div>
  );
}

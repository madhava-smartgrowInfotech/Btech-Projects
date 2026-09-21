import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Cpu, Dices, Gauge, LineChart as LineIcon, Repeat, ShieldCheck, Timer } from "lucide-react";
import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { ChartCard, ChartTooltip, SERIES, STATUS, StatTile, axisProps, barProps, gridProps } from "@/components/charts/ChartKit";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/common/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { formatDateTime, formatDuration, formatNumber, formatPercent } from "@/lib/format";
import type { EngineInfo, PlanAnalytics, PlanSummary } from "@/lib/types";

const METHOD_COLOUR: Record<string, string> = {
  SeatWise: SERIES[0],
  Sequential: SERIES[1],
  "Round-robin": SERIES[2],
  "Random shuffle": SERIES[3],
};
const METHODS = Object.keys(METHOD_COLOUR);

// ------------------------------------------------------------------ plan tab

function PlanTab() {
  const [params, setParams] = useSearchParams();
  const plans = useQuery({ queryKey: ["plans", "all"], queryFn: async () => (await api.get<PlanSummary[]>("/plans")).data });
  const usable = (plans.data ?? []).filter((p) => p.status !== "archived");
  const planId = Number(params.get("plan")) || usable.find((p) => p.status === "published")?.id || usable[0]?.id;
  const data = useQuery({
    queryKey: ["analytics", "plan", planId],
    queryFn: async () => (await api.get<PlanAnalytics>(`/analytics/plans/${planId}`)).data,
    enabled: Boolean(planId),
  });

  if (plans.isPending) return <CardsSkeleton count={3} />;
  if (plans.isError) return <ErrorState error={plans.error} onRetry={() => plans.refetch()} />;
  if (!usable.length)
    return (
      <EmptyState icon={LineIcon} title="No plans to analyse yet" description="Generate a plan for a sitting first."
        action={<Button asChild><Link to="/app/sessions">Go to sittings</Link></Button>} />
    );

  const a = data.data;
  const comparison = (a?.comparison ?? []).map((c) => ({ ...c, baseline: c.baseline ?? 0 }));
  const halls = (a?.halls ?? []).map((h) => ({ name: h.hall, utilisation: Math.round(h.utilisation * 100), placed: h.placed, seats: h.seats }));
  const depts = a?.department_codes ?? [];
  const deptRows = (a?.halls ?? []).map((h) => ({ name: h.hall, ...h.departments }));
  const attendance = (a?.attendance ?? []).map((h) => ({ name: h.hall, present: h.present, absent: h.absent, unmarked: Math.max(0, h.total - h.present - h.absent) }));

  return (
    <div className="space-y-6">
      <Select value={planId ? String(planId) : undefined} onValueChange={(v) => setParams({ tab: "plan", plan: v }, { replace: true })}>
        <SelectTrigger className="max-w-md" aria-label="Plan">
          <SelectValue placeholder="Choose a plan" />
        </SelectTrigger>
        <SelectContent>
          {usable.map((p) => (
            <SelectItem key={p.id} value={String(p.id)}>{p.session.label} · v{p.version} ({p.status})</SelectItem>
          ))}
        </SelectContent>
      </Select>

      {data.isPending && <Skeleton className="h-72 w-full rounded-xl" />}
      {data.isError && <ErrorState error={data.error} onRetry={() => data.refetch()} />}
      {a && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatTile icon={ShieldCheck} label="Same-paper neighbours" value={formatNumber(a.plan.same_paper_pairs)} tone={a.plan.same_paper_pairs === 0 ? "good" : "bad"}
              hint={`${formatNumber(a.plan.conflicts_avoided)} avoided vs roll order`} />
            <StatTile icon={Timer} label="Solve time" value={formatDuration(a.plan.solve_ms)} hint={`${formatNumber(a.plan.candidates)} candidates`} />
            <StatTile icon={Gauge} label="Seats filled" value={formatPercent(a.plan.utilisation)} hint={`${a.plan.halls_used} halls used`} />
            <StatTile icon={Repeat} label="Neighbour pairs" value={formatNumber(a.neighbour_pairs.total)}
              hint={`${formatNumber(a.neighbour_pairs.mixed)} mixed · ${formatNumber(a.neighbour_pairs.same_department)} same department`} />
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <ChartCard
              title="SeatWise compared with roll-order seating"
              description="Neighbour pairs breaking each rule. Roll order = the same candidates and halls seated in roll-number order."
              legend={[{ label: "SeatWise", color: SERIES[0] }, { label: "Roll order", color: SERIES[1] }]}
              table={{ columns: ["Measure", "SeatWise", "Roll order"], rows: comparison.map((c) => [c.measure, c.seatwise, c.baseline]) }}
            >
              <ResponsiveContainer>
                <BarChart data={comparison} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="measure" {...axisProps} interval={0} tick={{ ...axisProps.tick, fontSize: 10 }} />
                  <YAxis {...axisProps} />
                  <Tooltip content={<ChartTooltip format={(v) => formatNumber(Number(v))} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                  <Bar dataKey="seatwise" name="SeatWise" fill={SERIES[0]} {...barProps}>
                    <LabelList dataKey="seatwise" position="top" fill="hsl(var(--foreground))" fontSize={11} />
                  </Bar>
                  <Bar dataKey="baseline" name="Roll order" fill={SERIES[1]} {...barProps} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard
              title="Seats filled per hall"
              table={{ columns: ["Hall", "Seats filled %", "Candidates", "Seats"], rows: halls.map((h) => [h.name, h.utilisation, h.placed, h.seats]) }}
            >
              <ResponsiveContainer>
                <BarChart data={halls} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="name" {...axisProps} />
                  <YAxis {...axisProps} domain={[0, 100]} unit="%" />
                  <Tooltip content={<ChartTooltip format={(v) => `${v}%`} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                  <Bar dataKey="utilisation" name="Seats filled" fill={SERIES[0]} {...barProps} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard
              title="Departments in each hall"
              description="Department mix spreads each department over several halls"
              legend={depts.slice(0, 8).map((d, i) => ({ label: d, color: SERIES[i] }))}
              table={{ columns: ["Hall", ...depts], rows: deptRows.map((r) => [r.name, ...depts.map((d) => Number((r as Record<string, unknown>)[d] ?? 0))]) }}
            >
              <ResponsiveContainer>
                <BarChart data={deptRows} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="name" {...axisProps} />
                  <YAxis {...axisProps} allowDecimals={false} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                  {depts.slice(0, 8).map((d, i) => (
                    <Bar key={d} dataKey={d} name={d} stackId="d" fill={SERIES[i]} {...barProps} radius={i === Math.min(depts.length, 8) - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
            <ChartCard
              title="Attendance per hall"
              legend={[{ label: "Present", color: STATUS.good }, { label: "Absent", color: STATUS.bad }, { label: "To mark", color: STATUS.neutral }]}
              table={{ columns: ["Hall", "Present", "Absent", "To mark"], rows: attendance.map((h) => [h.name, h.present, h.absent, h.unmarked]) }}
            >
              <ResponsiveContainer>
                <BarChart data={attendance} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="name" {...axisProps} />
                  <YAxis {...axisProps} allowDecimals={false} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                  <Bar dataKey="present" name="Present" stackId="a" fill={STATUS.good} {...barProps} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="absent" name="Absent" stackId="a" fill={STATUS.bad} {...barProps} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="unmarked" name="To mark" stackId="a" fill={STATUS.neutral} {...barProps} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ engine tab

function AuthImage({ src, alt }: { src: string; alt: string }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let revoke: string | null = null;
    api.get<Blob>(src.replace(/^\/api/, ""), { responseType: "blob" }).then((r) => {
      revoke = URL.createObjectURL(r.data);
      setUrl(revoke);
    }).catch(() => setUrl(null));
    return () => {
      if (revoke) URL.revokeObjectURL(revoke);
    };
  }, [src]);
  if (!url) return <Skeleton className="aspect-video w-full" />;
  return <img src={url} alt={alt} className="w-full rounded-lg border bg-white" loading="lazy" />;
}

function EngineTab() {
  const engine = useQuery({ queryKey: ["analytics", "engine"], queryFn: async () => (await api.get<EngineInfo>("/analytics/engine")).data });
  if (engine.isPending) return <CardsSkeleton count={4} />;
  if (engine.isError) return <ErrorState error={engine.error} onRetry={() => engine.refetch()} />;
  const e = engine.data;
  if (!e.available || !e.metrics)
    return (
      <EmptyState icon={Cpu} title="No benchmark run found"
        description="Run the engine benchmark (venv\Scripts\python -m ml.benchmark) to see its results here." />
    );
  const m = e.metrics;
  const h = m.headline;
  const sizes = m.dataset.scenarios.filter((s) => /^(xs|s|m|l|xl)-\d+$/.test(s.name)).sort((a, b) => a.candidates - b.candidates);
  const row = (scenario: string, method: string) => m.summary.find((r) => r.scenario === scenario && r.method === method);
  const solve = sizes.map((s) => {
    const r = row(s.name, "SeatWise");
    return { name: formatNumber(s.candidates), seconds: r?.solve_s_mean ?? 0, min: r?.solve_s_min ?? 0, max: r?.solve_s_max ?? 0, halls: s.halls };
  });
  const conflicts = sizes.map((s) => ({
    name: formatNumber(s.candidates),
    ...Object.fromEntries(METHODS.map((meth) => [meth, row(s.name, meth)?.same_paper_pairs_mean ?? 0])),
  }));
  const predict = METHODS.map((meth) => ({
    name: meth,
    correlation: m.predictability[meth]?.abs_roll_seat_correlation ?? 0,
    overlap: (m.predictability[meth]?.neighbour_overlap ?? 0) * 100,
  }));
  const scenarioTotal = m.summary.filter((r) => r.method === "SeatWise");

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile icon={CheckCircle2} label="Hard rules satisfied" value={h.all_hard_rules_satisfied ? "100%" : formatPercent(h.hard_rules_satisfied_rate)}
          tone={h.all_hard_rules_satisfied ? "good" : "bad"} hint={`${scenarioTotal.length} scenarios × ${m.dataset.seeds.length} seeds, every plan validated independently`} />
        <StatTile icon={Timer} label={`Solve time, ${formatNumber(h.candidates)} candidates`} value={`${h.solve_s_mean.toFixed(1)} s`}
          hint={`slowest scenario ${h.max_solve_s.toFixed(1)} s`} />
        <StatTile icon={ShieldCheck} label="Conflicts avoided vs roll order" value={formatNumber(h.conflicts_avoided_vs_sequential)}
          hint={`${h.same_paper_pairs} same-paper neighbours left`} tone="good" />
        <StatTile icon={Dices} label="Roll-to-seat correlation" value={h.abs_roll_seat_correlation.toFixed(2)}
          hint={`${formatPercent(h.neighbour_overlap, 1)} of neighbours repeat with a new seed`} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartCard title="Solve time by session size" description="Mean over seeds, CP-SAT on this PC"
          table={{ columns: ["Candidates", "Mean s", "Fastest s", "Slowest s", "Halls available"], rows: solve.map((s) => [s.name, s.seconds.toFixed(2), s.min.toFixed(2), s.max.toFixed(2), s.halls]) }}>
          <ResponsiveContainer>
            <LineChart data={solve} margin={{ top: 12, right: 16, left: -12, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="name" {...axisProps} />
              <YAxis {...axisProps} unit=" s" />
              <Tooltip content={<ChartTooltip format={(v) => `${Number(v).toFixed(2)} s`} labelFormat={(l) => `${l} candidates`} />} />
              <Line type="monotone" dataKey="seconds" name="Solve time" stroke={SERIES[0]} strokeWidth={2} dot={{ r: 4, fill: SERIES[0], stroke: "hsl(var(--card))", strokeWidth: 2 }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Same-paper neighbour pairs" description="By session size and method (lower is better)"
          legend={METHODS.map((meth) => ({ label: meth, color: METHOD_COLOUR[meth] }))}
          table={{ columns: ["Candidates", ...METHODS], rows: conflicts.map((c) => [c.name, ...METHODS.map((meth) => Math.round(Number((c as Record<string, unknown>)[meth])))]) }}>
          <ResponsiveContainer>
            <BarChart data={conflicts} margin={{ top: 8, right: 8, left: -4, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="name" {...axisProps} />
              <YAxis {...axisProps} />
              <Tooltip content={<ChartTooltip format={(v) => formatNumber(Math.round(Number(v)))} labelFormat={(l) => `${l} candidates`} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
              {METHODS.map((meth) => (
                <Bar key={meth} dataKey={meth} name={meth} fill={METHOD_COLOUR[meth]} {...barProps} maxBarSize={16} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Can a seat be guessed from the roll number?" description="Rank correlation between roll order and seat order (0 = unpredictable)"
          table={{ columns: ["Method", "|correlation|"], rows: predict.map((p) => [p.name, p.correlation.toFixed(3)]) }} height={220}>
          <ResponsiveContainer>
            <BarChart data={predict} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid {...gridProps} vertical horizontal={false} />
              <XAxis type="number" domain={[0, 1]} {...axisProps} />
              <YAxis type="category" dataKey="name" {...axisProps} width={96} />
              <Tooltip content={<ChartTooltip format={(v) => Number(v).toFixed(3)} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
              <Bar dataKey="correlation" name="|correlation|" {...barProps} radius={[0, 4, 4, 0]}>
                {predict.map((p) => <Cell key={p.name} fill={METHOD_COLOUR[p.name]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Do the same people sit together again?" description="Neighbour pairs repeated between plans made with different seeds"
          table={{ columns: ["Method", "Repeated %"], rows: predict.map((p) => [p.name, p.overlap.toFixed(1)]) }} height={220}>
          <ResponsiveContainer>
            <BarChart data={predict} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid {...gridProps} vertical horizontal={false} />
              <XAxis type="number" domain={[0, 100]} unit="%" {...axisProps} />
              <YAxis type="category" dataKey="name" {...axisProps} width={96} />
              <Tooltip content={<ChartTooltip format={(v) => `${Number(v).toFixed(1)}%`} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
              <Bar dataKey="overlap" name="Repeated" {...barProps} radius={[0, 4, 4, 0]}>
                {predict.map((p) => <Cell key={p.name} fill={METHOD_COLOUR[p.name]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Every scenario</CardTitle>
          <CardDescription>Means over {m.dataset.seeds.length} seeds. Hard rules: same-paper neighbours, roll-gap and accessible seats.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="normal-case">Scenario</TableHead>
                <TableHead className="normal-case">Method</TableHead>
                <TableHead className="normal-case">Solve s</TableHead>
                <TableHead className="normal-case">Same paper</TableHead>
                <TableHead className="normal-case">Roll gap</TableHead>
                <TableHead className="normal-case">Accessible</TableHead>
                <TableHead className="normal-case">Same dept.</TableHead>
                <TableHead className="normal-case">Hard rules</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {m.summary.map((r) => (
                <TableRow key={`${r.scenario}-${r.method}`}>
                  <TableCell className="font-mono text-xs">{r.scenario}</TableCell>
                  <TableCell className="text-xs">
                    <span className="inline-flex items-center gap-1.5">
                      <span className="size-2 rounded-sm" style={{ background: METHOD_COLOUR[r.method] }} />
                      {r.method}
                    </span>
                  </TableCell>
                  <TableCell className="tabular text-xs">{r.solve_s_mean.toFixed(2)}</TableCell>
                  <TableCell className="tabular text-xs">{Math.round(r.same_paper_pairs_mean ?? 0)}</TableCell>
                  <TableCell className="tabular text-xs">{Math.round(r.roll_gap_violations_mean ?? 0)}</TableCell>
                  <TableCell className="tabular text-xs">{Math.round(r.accessible_violations_mean ?? 0)}</TableCell>
                  <TableCell className="tabular text-xs">{Math.round(r.same_department_pairs_mean ?? 0)}</TableCell>
                  <TableCell>
                    {r.hard_rules_satisfied_rate === 1 ? <Badge variant="success">All met</Badge> : <Badge variant="destructive">{formatPercent(r.hard_rules_satisfied_rate)}</Badge>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        {m.tuning && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Time budget tuning</CardTitle>
              <CardDescription>
                The fastest per-hall budget whose department mix is within {Math.round(m.tuning.tolerance * 100)}% of the best is used:{" "}
                <strong>{m.tuning.chosen_budget}</strong>.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="normal-case">Budget</TableHead>
                    <TableHead className="normal-case">Same-dept. pairs</TableHead>
                    <TableHead className="normal-case">Session solve s</TableHead>
                    <TableHead className="normal-case">Hard rules</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {m.tuning.budgets.map((b) => (
                    <TableRow key={b.budget} className={b.budget === m.tuning!.chosen_budget ? "bg-primary/5" : undefined}>
                      <TableCell className="tabular text-xs font-medium">{b.budget}{b.budget === m.tuning!.chosen_budget && " (chosen)"}</TableCell>
                      <TableCell className="tabular text-xs">{b.same_department_pairs_mean.toFixed(1)}</TableCell>
                      <TableCell className="tabular text-xs">{b.session_solve_s_mean.toFixed(2)}</TableCell>
                      <TableCell className="text-xs">{b.all_hard_rules_satisfied ? "All met" : "Missed"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">About this run</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {[
              ["Run", m.run],
              ["Date", formatDateTime(m.run_date)],
              ["Engine", `SeatWise engine ${m.engine_version} · OR-Tools CP-SAT ${m.ortools_version}`],
              ["Budget in use", `${e.profile.hall_budget_in_use} per hall (${e.profile.source})`],
              ["Machine", `${m.machine.cpu_threads} CPU threads · Python ${m.machine.python}`],
              ["Data", m.dataset.type],
              ["Split", m.dataset.split],
            ].map(([k, v]) => (
              <div key={k} className="grid grid-cols-[7rem_1fr] gap-3">
                <span className="text-muted-foreground">{k}</span>
                <span className="break-words">{v}</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {e.plots.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Charts saved with the run</CardTitle>
            <CardDescription>The PNG files in experiments/{m.run}/.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            {e.plots.map((src) => (
              <AuthImage key={src} src={src} alt={src.split("/").pop()!.replace(".png", "").replaceAll("_", " ")} />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") === "engine" ? "engine" : "plan";
  return (
    <>
      <PageHeader title="Analytics" description="How each plan performs, and how the seating engine performs on its benchmark." />
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList>
          <TabsTrigger value="plan"><LineIcon /> Plans</TabsTrigger>
          <TabsTrigger value="engine"><Cpu /> Engine performance</TabsTrigger>
        </TabsList>
        <TabsContent value="plan"><PlanTab /></TabsContent>
        <TabsContent value="engine"><EngineTab /></TabsContent>
      </Tabs>
    </>
  );
}

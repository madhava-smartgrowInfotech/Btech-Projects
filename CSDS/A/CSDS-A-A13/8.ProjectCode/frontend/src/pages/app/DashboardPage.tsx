import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  ArrowRight, CalendarClock, Check, ClipboardCheck, Globe, Grid3x3, ShieldCheck, Timer, Upload, UserCheck, Users,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard, ChartTooltip, STATUS, SERIES, StatTile, axisProps, barProps, gridProps } from "@/components/charts/ChartKit";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, ErrorState } from "@/components/common/States";
import { PlanStatusBadge } from "@/components/plans/PlanStatusBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatDuration, formatNumber, formatPercent, formatShortDate } from "@/lib/format";
import type { AttendanceAssignment, Overview, Rules } from "@/lib/types";
import { cn } from "@/lib/utils";

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
}

function Steps({ o }: { o: Overview }) {
  const steps = [
    { done: o.counts.candidates > 0, title: "Import your data", text: "Courses, halls, candidates and the timetable.", to: "/app/import", icon: Upload },
    { done: o.counts.plans > 0, title: "Generate seating plans", text: "One per sitting - solved in seconds.", to: "/app/sessions", icon: Grid3x3 },
    { done: o.counts.published > 0, title: "Publish", text: "Candidates can then look up their seats.", to: "/app/sessions", icon: Globe },
    { done: o.attendance.present + o.attendance.absent > 0, title: "Take attendance", text: "Invigilators mark each hall on a tablet.", to: "/app/attendance", icon: ClipboardCheck },
  ];
  if (steps.every((s) => s.done)) return null;
  const next = steps.findIndex((s) => !s.done);
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-base">Getting started</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {steps.map((s, i) => (
          <Link
            key={s.title}
            to={s.to}
            className={cn(
              "group flex gap-3 rounded-xl border p-4 transition-colors hover:border-primary/50",
              i === next && "border-primary bg-primary/5",
            )}
          >
            <span className={cn("flex size-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold", s.done && "border-success bg-success text-success-foreground")}>
              {s.done ? <Check className="size-4" /> : i + 1}
            </span>
            <span>
              <span className="block text-sm font-medium">{s.title}</span>
              <span className="text-xs text-muted-foreground">{s.text}</span>
            </span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}

function AdminDashboard() {
  const overview = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: async () => (await api.get<Overview>("/analytics/overview")).data,
    refetchInterval: 15_000,
  });
  if (overview.isPending) return <CardsSkeleton count={4} />;
  if (overview.isError) return <ErrorState error={overview.error} onRetry={() => overview.refetch()} />;
  const o = overview.data;

  const attendanceData = o.sessions
    .filter((s) => s.attendance)
    .map((s) => ({ name: `${formatShortDate(s.date)} ${s.start_time}`, present: s.attendance!.present, absent: s.attendance!.absent, unmarked: s.attendance!.unmarked }));
  const solveData = o.solve_times.filter((p) => p.status !== "archived").map((p) => ({ name: `v${p.version} · ${p.label.split(" · ")[0]}`, seconds: p.solve_ms / 1000, candidates: p.candidates }));
  const hallData = o.hall_usage.slice(0, 10).map((h) => ({ name: h.hall, utilisation: Math.round(h.utilisation * 100), sittings: h.sittings }));

  return (
    <>
      <Steps o={o} />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="md:col-span-2 xl:col-span-1 xl:row-span-2">
          <StatTile
            hero
            icon={ShieldCheck}
            label="Same-paper neighbours avoided"
            value={formatNumber(o.totals.conflicts_avoided)}
            hint={`across ${o.counts.published} published sitting${o.counts.published === 1 ? "" : "s"}, compared with roll-order seating. Remaining: ${o.totals.same_paper_pairs}.`}
          />
        </motion.div>
        <StatTile icon={Users} label="Candidates seated" value={formatNumber(o.counts.seated)} hint={`${formatNumber(o.counts.candidates)} candidates imported`} />
        <StatTile icon={CalendarClock} label="Sittings published" value={`${o.counts.published} / ${o.counts.sessions}`} hint={`${o.counts.plans} plan versions in total`} />
        <StatTile icon={Timer} label="Average solve time" value={o.totals.avg_solve_ms ? formatDuration(o.totals.avg_solve_ms) : "-"}
          hint={o.totals.max_solve_ms ? `slowest ${formatDuration(o.totals.max_solve_ms)}` : "no plans yet"} />
        <StatTile icon={UserCheck} label="Attendance" value={o.attendance.rate !== null ? formatPercent(o.attendance.rate) : "-"}
          hint={`${formatNumber(o.attendance.present)} present · ${formatNumber(o.attendance.absent)} absent · ${formatNumber(o.attendance.unmarked)} to mark`} />
        <StatTile icon={ShieldCheck} label="Plans meeting every rule" value={o.totals.hard_ok_rate !== null ? formatPercent(o.totals.hard_ok_rate) : "-"}
          hint={`${o.totals.manual_moves} manual seat moves, all logged`} tone={o.totals.hard_ok_rate === 1 ? "good" : undefined} />
        <StatTile icon={Grid3x3} label="Halls" value={formatNumber(o.counts.halls)} hint={`${o.hall_usage.length} used by published plans`} />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <ChartCard
          title="Attendance by sitting"
          description="Published plans only"
          legend={[{ label: "Present", color: STATUS.good }, { label: "Absent", color: STATUS.bad }, { label: "To mark", color: STATUS.neutral }]}
          table={{ columns: ["Sitting", "Present", "Absent", "To mark"], rows: attendanceData.map((d) => [d.name, d.present, d.absent, d.unmarked]) }}
        >
          {attendanceData.length ? (
            <ResponsiveContainer>
              <BarChart data={attendanceData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis {...axisProps} allowDecimals={false} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                <Bar dataKey="present" name="Present" stackId="a" fill={STATUS.good} {...barProps} radius={[0, 0, 0, 0]} />
                <Bar dataKey="absent" name="Absent" stackId="a" fill={STATUS.bad} {...barProps} radius={[0, 0, 0, 0]} />
                <Bar dataKey="unmarked" name="To mark" stackId="a" fill={STATUS.neutral} {...barProps} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">Publish a plan to track attendance.</p>
          )}
        </ChartCard>
        <ChartCard
          title="Solve time per plan"
          description="Seconds from request to a validated plan"
          table={{ columns: ["Plan", "Seconds", "Candidates"], rows: solveData.map((d) => [d.name, d.seconds.toFixed(1), d.candidates]) }}
        >
          {solveData.length ? (
            <ResponsiveContainer>
              <BarChart data={solveData} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} interval={0} tick={{ ...axisProps.tick, fontSize: 10 }} />
                <YAxis {...axisProps} unit=" s" />
                <Tooltip content={<ChartTooltip format={(v) => `${Number(v).toFixed(1)} s`} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                <Bar dataKey="seconds" name="Solve time" fill={SERIES[0]} {...barProps} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No plans yet.</p>
          )}
        </ChartCard>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-[1fr_24rem]">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="text-base">Sittings</CardTitle>
            <Button asChild variant="ghost" size="sm">
              <Link to="/app/sessions">All sittings <ArrowRight /></Link>
            </Button>
          </CardHeader>
          <CardContent className="divide-y p-0">
            {o.sessions.length === 0 && <p className="p-5 text-sm text-muted-foreground">No timetable imported yet.</p>}
            {o.sessions.map((s) => (
              <Link key={s.id} to={`/app/sessions/${s.id}`} className="flex items-center gap-4 px-5 py-3 transition-colors hover:bg-muted/50">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{s.label}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatNumber(s.candidates)} candidates · {s.papers} papers
                    {s.published_plan && ` · ${s.published_plan.halls_used} halls · ${formatDuration(s.published_plan.solve_ms)}`}
                  </div>
                </div>
                {s.attendance && s.attendance.total > 0 && (
                  <Badge variant="outline" className="hidden sm:inline-flex">
                    {Math.round(((s.attendance.present + s.attendance.absent) / s.attendance.total) * 100)}% marked
                  </Badge>
                )}
                <PlanStatusBadge status={s.published_plan ? "published" : s.plans ? "draft" : null} />
              </Link>
            ))}
          </CardContent>
        </Card>
        <ChartCard
          title="Busiest halls"
          description="Average share of seats filled in published plans"
          table={{ columns: ["Hall", "Seats filled %", "Sittings"], rows: hallData.map((h) => [h.name, h.utilisation, h.sittings]) }}
          height={Math.max(160, hallData.length * 30)}
        >
          {hallData.length ? (
            <ResponsiveContainer>
              <BarChart data={hallData} layout="vertical" margin={{ top: 0, right: 16, left: 4, bottom: 0 }}>
                <CartesianGrid {...gridProps} vertical horizontal={false} />
                <XAxis type="number" domain={[0, 100]} {...axisProps} unit="%" />
                <YAxis type="category" dataKey="name" {...axisProps} width={56} />
                <Tooltip content={<ChartTooltip format={(v) => `${v}%`} />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                <Bar dataKey="utilisation" name="Seats filled" fill={SERIES[0]} {...barProps} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No published plans yet.</p>
          )}
        </ChartCard>
      </div>
    </>
  );
}

function InvigilatorDashboard() {
  const mine = useQuery({
    queryKey: ["attendance", "assignments"],
    queryFn: async () => (await api.get<AttendanceAssignment[]>("/attendance/assignments")).data,
  });
  const rules = useQuery({ queryKey: ["rules"], queryFn: async () => (await api.get<Rules>("/settings/rules")).data });
  if (mine.isPending) return <CardsSkeleton count={3} />;
  if (mine.isError) return <ErrorState error={mine.error} onRetry={() => mine.refetch()} />;
  const next = mine.data.find((a) => !a.submitted_at);
  return (
    <div className="space-y-6">
      {next ? (
        <Card className="border-primary/40 bg-primary/5">
          <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-xs font-medium uppercase tracking-wider text-primary">Next hall</div>
              <div className="mt-1 font-display text-2xl font-semibold">{next.hall.code} · {next.hall.name}</div>
              <div className="text-sm text-muted-foreground">
                {next.session.label} · {formatDate(next.session.date)} {next.session.start_time}-{next.session.end_time} · {next.total} candidates
              </div>
            </div>
            <Button asChild size="lg">
              <Link to={`/app/attendance/${next.plan_id}/${next.hall.id}`}>Take attendance <ArrowRight /></Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            {mine.data.length ? "Every register you supervise has been submitted. Thank you." : "No halls are assigned to you yet. They appear here once a plan is published."}
          </CardContent>
        </Card>
      )}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile icon={Grid3x3} label="My halls" value={String(mine.data.length)} />
        <StatTile icon={UserCheck} label="Marked present" value={formatNumber(mine.data.reduce((n, a) => n + a.present, 0))} />
        <StatTile icon={ShieldCheck} label="Neighbourhood rule"
          value={rules.data ? `${rules.data.adjacency} seats` : "-"} hint="around each candidate never share a paper" />
      </div>
      {mine.data.length > 0 && (
        <Button asChild variant="outline">
          <Link to="/app/attendance">All my halls <ArrowRight /></Link>
        </Button>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  return (
    <>
      <PageHeader
        title={`${greeting()}, ${user?.full_name.split(" ")[0]}`}
        description={user?.role === "admin" ? "Your seating workspace at a glance." : "Your halls and registers."}
      />
      {user?.role === "admin" ? <AdminDashboard /> : <InvigilatorDashboard />}
    </>
  );
}

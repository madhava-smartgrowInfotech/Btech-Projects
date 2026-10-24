import { Activity, BarChart3, Camera, PieChart as PieIcon, ScanSearch, TrendingUp } from "lucide-react";
import { Link } from "react-router";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps, SERIES } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { SEVERITY_COLOR, SEVERITY_LABEL } from "@/lib/disease";
import { useLang } from "@/lib/i18n";
import { useAnalytics } from "@/lib/queries";
import type { Severity } from "@/lib/api";

const SEVERITIES: Severity[] = ["high", "medium", "low", "none"];

export default function Analytics() {
  const { t } = useLang();
  const q = useAnalytics();

  if (q.isError) return <ErrorState error={q.error} title="Couldn't load analytics" onRetry={() => q.refetch()} />;

  const d = q.data;
  const dist = d ? Object.entries(d.disease_distribution).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count) : [];
  const sev = d ? SEVERITIES.map((s) => ({ key: s, name: SEVERITY_LABEL[s], value: d.severity[s] ?? 0 })).filter((s) => s.value > 0) : [];
  const timeline = d?.timeline ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("analytics.title", "Farm analytics")}
        description={d ? `${d.total_detections} total scan${d.total_detections === 1 ? "" : "s"} · data for crop decisions` : "Patterns across your scans."}
      />

      {q.isPending ? (
        <div className="grid gap-4 md:grid-cols-2" role="status" aria-label="Loading analytics">
          <Skeleton className="h-80 rounded-2xl" />
          <Skeleton className="h-80 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl md:col-span-2" />
        </div>
      ) : d && d.total_detections === 0 ? (
        <EmptyState
          icon={<BarChart3 />}
          title="Nothing to chart yet"
          description="Analytics are built from your scans. Run your first diagnosis and the charts will fill in."
          action={
            <Button asChild>
              <Link to="/detect">
                <Camera /> Scan a leaf
              </Link>
            </Button>
          }
        />
      ) : (
        d && (
          <>
            <Stagger className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <StaggerItem>
                <StatCard label="Total scans" value={d.total_detections} icon={<ScanSearch />} />
              </StaggerItem>
              <StaggerItem>
                <StatCard label="Different diseases" value={dist.length} icon={<Activity />} accent="cyan" />
              </StaggerItem>
              <StaggerItem>
                <StatCard label="High severity" value={d.severity.high ?? 0} icon={<TrendingUp />} accent="magenta" />
              </StaggerItem>
              <StaggerItem>
                <StatCard label="Healthy" value={d.severity.none ?? 0} icon={<PieIcon />} accent="cyan" />
              </StaggerItem>
            </Stagger>

            <div className="grid gap-4 md:grid-cols-2">
              <ChartCard
                title="Disease distribution"
                description="How many times each diagnosis appeared"
                icon={<BarChart3 />}
                table={{ columns: ["Diagnosis", "Scans"], rows: dist.map((x) => [x.name, x.count]) }}
              >
                <div className="h-72" role="img" aria-label={`Bar chart of scans per diagnosis: ${dist.map((x) => `${x.name} ${x.count}`).join(", ")}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dist} layout="vertical" margin={{ left: 0, right: 16 }}>
                      <ChartGradients id="d" />
                      <CartesianGrid {...gridProps} horizontal={false} vertical />
                      <XAxis type="number" allowDecimals={false} {...axisProps} />
                      <YAxis type="category" dataKey="name" width={170} interval={0} {...axisProps} tickFormatter={(v: string) => (v.length > 26 ? `${v.slice(0, 25)}…` : v)} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--muted)" }} />
                      <Bar dataKey="count" name="Scans" fill={SERIES[0]} radius={[0, 8, 8, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              <ChartCard
                title="Severity breakdown"
                description="Share of scans by how serious the diagnosis is"
                icon={<PieIcon />}
                legend={sev.map((s) => ({ label: `${s.name} (${s.value})`, color: SEVERITY_COLOR[s.key] }))}
                table={{ columns: ["Severity", "Scans"], rows: sev.map((s) => [s.name, s.value]) }}
              >
                <div className="h-64" role="img" aria-label={`Donut chart of severity: ${sev.map((s) => `${s.name} ${s.value}`).join(", ")}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={sev} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={3} stroke="none">
                        {sev.map((s) => (
                          <Cell key={s.key} fill={SEVERITY_COLOR[s.key]} />
                        ))}
                      </Pie>
                      <Tooltip content={<ChartTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>

              <ChartCard
                className="md:col-span-2"
                title="Detection timeline"
                description="Scans per day"
                icon={<TrendingUp />}
                table={{ columns: ["Date", "Scans"], rows: timeline.map((x) => [x.date, x.count]) }}
              >
                <div className="h-64" role="img" aria-label={`Line chart of scans per day: ${timeline.map((x) => `${x.date} ${x.count}`).join(", ")}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeline} margin={{ left: -16, right: 8, top: 8 }}>
                      <ChartGradients id="t" />
                      <CartesianGrid {...gridProps} />
                      <XAxis dataKey="date" {...axisProps} />
                      <YAxis allowDecimals={false} {...axisProps} />
                      <Tooltip content={<ChartTooltip />} />
                      <Area type="monotone" dataKey="count" name="Scans" stroke={SERIES[0]} strokeWidth={2.5} fill="url(#areat-0)" dot={{ r: 3, fill: SERIES[0] }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </ChartCard>
            </div>
          </>
        )
      )}
    </div>
  );
}

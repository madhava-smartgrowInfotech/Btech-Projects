import { useState } from "react";
import { Link } from "react-router-dom";
import { BarChart3, Clock3, FileWarning, MapPinned, ShieldCheck } from "lucide-react";
import { ClassShareChart, ComplaintFlowChart, StatTile, TimeOfDayHeatmap } from "@/components/charts/charts";
import { StatusBadge } from "@/components/complaints/parts";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { ZoneBar } from "@/components/common/zone";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { apiError } from "@/lib/api";
import { hoursText, useFunnel, useOperators, useSummary, useTimeOfDay, useTrends, useWorst, type AnalyticsFilters } from "@/lib/analytics";
import { STATUS_LABEL, type ComplaintStatus } from "@/lib/complaints";
import { useCoverageSummary } from "@/lib/coverage";
import { safeStorage } from "@/lib/utils";

const KEY = "signalscout-analytics-filters";
const PERIODS = [{ v: "7", l: "Last 7 days" }, { v: "30", l: "Last 30 days" }, { v: "90", l: "Last 90 days" }, { v: "all", l: "All time" }];

function load(): AnalyticsFilters {
  try {
    return { operator: null, days: 90, includeSample: true, ...JSON.parse(safeStorage.get(KEY) || "{}") };
  } catch {
    return { operator: null, days: 90, includeSample: true };
  }
}

function Block({ title, description, children, className }: { title: string; description?: string; children: React.ReactNode; className?: string }) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function Analytics() {
  const [f, setF] = useState<AnalyticsFilters>(load);
  const set = (patch: Partial<AnalyticsFilters>) => setF((prev) => { const next = { ...prev, ...patch }; safeStorage.set(KEY, JSON.stringify(next)); return next; });
  const cov = useCoverageSummary();
  const summary = useSummary(f);
  const trends = useTrends(f);
  const worst = useWorst(f);
  const tod = useTimeOfDay(f);
  const ops = useOperators(f);
  const funnel = useFunnel(f);
  const s = summary.data;

  return (
    <>
      <PageHeader title="Analytics" description="Where and when service fails, how operators compare, and how quickly complaints are resolved." />
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Select value={f.operator ?? "all"} onValueChange={(v) => set({ operator: v === "all" ? null : v })}>
          <SelectTrigger className="sm:w-52" aria-label="Operator"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All operators</SelectItem>
            {cov.data?.operators.map((o) => <SelectItem key={o.name} value={o.name}>{o.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={f.days ? String(f.days) : "all"} onValueChange={(v) => set({ days: v === "all" ? null : Number(v) })}>
          <SelectTrigger className="sm:w-44" aria-label="Period"><SelectValue /></SelectTrigger>
          <SelectContent>{PERIODS.map((p) => <SelectItem key={p.v} value={p.v}>{p.l}</SelectItem>)}</SelectContent>
        </Select>
        <label className="flex items-center gap-2 text-sm"><Switch checked={f.includeSample} onCheckedChange={(v) => set({ includeSample: v })} /> Include sample data</label>
      </div>

      {summary.isError ? <ErrorState message={apiError(summary.error)} onRetry={() => summary.refetch()} /> : (
        <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {!s ? [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />) : (
            <>
              <StatTile icon={<MapPinned className="h-4 w-4" />} label="Zones monitored" value={s.zones_monitored.toLocaleString()} hint={`${s.readings_total.toLocaleString()} readings in total`} />
              <StatTile icon={<BarChart3 className="h-4 w-4" />} label="Weak or dead zones" value={s.bad_zone_share != null ? `${Math.round(s.bad_zone_share * 100)}%` : "–"} tone={s.bad_zone_share && s.bad_zone_share > 0.3 ? "bad" : undefined} hint={`${s.zones_dead} dead, ${s.zones_bad - s.zones_dead} weak`} />
              <StatTile icon={<FileWarning className="h-4 w-4" />} label="Complaints this week" value={s.complaints_registered_7d} hint={`${s.complaints_open} open · ${s.complaints_needing_action} waiting for action`} />
              <StatTile icon={<Clock3 className="h-4 w-4" />} label="Median time to resolve" value={hoursText(s.median_hours_to_resolve)} hint={`${s.complaints_verified} fixes verified${s.median_hours_to_verify != null ? ` · verified in ${hoursText(s.median_hours_to_verify)}` : ""}`} />
            </>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Block title="Service quality over time" description="Share of readings in each class per day. A growing red band means more dead-zone readings.">
          {trends.isPending ? <Skeleton className="h-60" /> : trends.isError ? <ErrorState message={apiError(trends.error)} /> :
            trends.data.some((d) => d.readings) ? <ClassShareChart data={trends.data} height={260} /> : <p className="py-16 text-center text-sm text-muted-foreground">No readings in this period.</p>}
        </Block>
        <Block title="Complaints" description="Registered and resolved per day.">
          {trends.isPending ? <Skeleton className="h-56" /> : trends.isError ? <ErrorState message={apiError(trends.error)} /> : <ComplaintFlowChart data={trends.data} />}
        </Block>
      </div>

      <Block className="mt-4" title="When service fails" description="Share of weak or dead readings by weekday and hour, in your local time.">
        {tod.isPending ? <Skeleton className="h-52" /> : tod.isError ? <ErrorState message={apiError(tod.error)} /> :
          tod.data.length ? <TimeOfDayHeatmap cells={tod.data} /> : <p className="py-10 text-center text-sm text-muted-foreground">No readings in this period.</p>}
      </Block>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Block title="Worst areas" description="Zones with at least 15 readings, ranked by the share of weak or dead readings.">
          {worst.isPending ? <Skeleton className="h-64" /> : worst.isError ? <ErrorState message={apiError(worst.error)} /> : !worst.data.length ? (
            <EmptyState icon={ShieldCheck} title="No problem areas" description="No zone has enough readings in this period yet." className="py-8" />
          ) : (
            <ol className="divide-y">
              {worst.data.map((w, i) => (
                <li key={`${w.cell}-${w.operator}`} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center">
                  <span className="w-6 shrink-0 font-mono text-sm text-muted-foreground">{i + 1}</span>
                  <div className="min-w-0 flex-1">
                    <p className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="font-medium">{w.operator}</span>
                      <span className="text-muted-foreground">{w.lat.toFixed(4)}, {w.lon.toFixed(4)} · {w.readings} readings</span>
                      {w.sources.includes("sample_dataset") && <Badge variant="secondary">Sample</Badge>}
                    </p>
                    <ZoneBar className="mt-1.5" strong={Math.round(w.readings * (1 - w.bad_share))} weak={Math.round(w.readings * (w.bad_share - w.dead_share))} dead={Math.round(w.readings * w.dead_share)} />
                  </div>
                  <div className="shrink-0 sm:w-40 sm:text-right">
                    {w.complaint ? <Link to={`/app/complaints/${w.complaint.id}`} className="inline-flex items-center gap-2 text-sm text-primary hover:underline">{w.complaint.ref_code} <StatusBadge status={w.complaint.status as ComplaintStatus} /></Link>
                      : <span className="text-xs text-muted-foreground">No open complaint</span>}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </Block>

        <div className="space-y-4">
          <Block title="Operators" description="Share of readings in each class, and complaint handling.">
            {ops.isPending ? <Skeleton className="h-40" /> : ops.isError ? <ErrorState message={apiError(ops.error)} /> : !ops.data.length ? <p className="text-sm text-muted-foreground">No readings yet.</p> : (
              <ul className="space-y-4">
                {ops.data.map((o) => (
                  <li key={o.operator}>
                    <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2 text-sm">
                      <span className="font-medium">{o.operator} {o.sources.length === 1 && o.sources[0] === "sample_dataset" && <Badge variant="secondary" className="ml-1">Sample</Badge>}</span>
                      <span className="text-xs text-muted-foreground tabular">{o.readings.toLocaleString()} readings · {o.zones} zones</span>
                    </div>
                    <ZoneBar strong={o.strong_share * 1000} weak={o.weak_share * 1000} dead={o.dead_share * 1000} />
                    <p className="mt-1 text-xs text-muted-foreground">
                      {[
                        o.median_latency != null && `latency ${Math.round(o.median_latency)} ms`,
                        o.median_dl != null && `download ${o.median_dl.toFixed(1)} Mbps`,
                        o.median_rsrp != null && `RSRP ${Math.round(o.median_rsrp)} dBm`,
                        `${o.complaints_total} ${o.complaints_total === 1 ? "complaint" : "complaints"} (${o.complaints_open} open)`,
                        o.median_hours_to_resolve != null && `resolved in ${hoursText(o.median_hours_to_resolve)}`,
                      ].filter(Boolean).join(" · ")}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Block>

          <Block title="Complaint funnel" description="How many complaints reached each stage, and the median time between stages.">
            {funnel.isPending ? <Skeleton className="h-40" /> : funnel.isError ? <ErrorState message={apiError(funnel.error)} /> : (
              <div className="space-y-2">
                {funnel.data.stages.map((st, i) => {
                  const max = Math.max(funnel.data.stages[0]!.reached, 1);
                  const gap = funnel.data.gaps[i - 1];
                  return (
                    <div key={st.stage}>
                      {gap && gap.median_hours != null && <p className="pl-2 text-[11px] text-muted-foreground">↓ median {hoursText(gap.median_hours)}</p>}
                      <div className="flex items-center gap-3">
                        <span className="w-28 shrink-0 text-xs">{STATUS_LABEL[st.stage as ComplaintStatus]}</span>
                        <div className="h-5 flex-1 rounded bg-muted">
                          <div className="h-5 rounded bg-[var(--series-1)]" style={{ width: `${(st.reached / max) * 100}%`, minWidth: st.reached ? 4 : 0 }} />
                        </div>
                        <span className="w-10 shrink-0 text-right text-xs tabular">{st.reached}</span>
                      </div>
                    </div>
                  );
                })}
                <p className="pt-1 text-xs text-muted-foreground">{funnel.data.dismissed} dismissed · {funnel.data.reopened} reopened after a fix</p>
              </div>
            )}
          </Block>
        </div>
      </div>
    </>
  );
}

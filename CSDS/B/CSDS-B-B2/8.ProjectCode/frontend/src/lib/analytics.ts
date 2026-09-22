import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export interface Summary {
  readings_total: number;
  readings_24h: number;
  zones_monitored: number;
  zones_bad: number;
  zones_dead: number;
  bad_zone_share: number | null;
  complaints_open: number;
  complaints_needing_action: number;
  complaints_registered_7d: number;
  complaints_verified: number;
  median_hours_to_resolve: number | null;
  median_hours_to_verify: number | null;
  devices_online: number;
  mine: { readings: number; complaints: number } | null;
}
export interface TrendDay { day: string; readings: number; strong: number; weak: number; dead: number; weak_share: number | null; dead_share: number | null; registered: number; resolved: number }
export interface WorstArea { cell: string; operator: string; readings: number; bad_share: number; dead_share: number; lat: number; lon: number; median_rsrp: number | null; median_latency: number | null; last: string; sources: string[]; complaint: { id: number; ref_code: string; status: string } | null }
export interface TodCell { weekday: number; hour: number; bad_share: number; readings: number }
export interface OperatorRow { operator: string; readings: number; zones: number; strong_share: number; weak_share: number; dead_share: number; median_rsrp: number | null; median_latency: number | null; median_dl: number | null; complaints_total: number; complaints_open: number; median_hours_to_resolve: number | null; sources: string[] }
export interface Funnel { stages: { stage: string; reached: number }[]; gaps: { from: string; to: string; median_hours: number | null }[]; dismissed: number; reopened: number }

export interface AnalyticsFilters { operator: string | null; days: number | null; includeSample: boolean }

const tz = () => -new Date().getTimezoneOffset();
const params = (f: AnalyticsFilters, extra: Record<string, unknown> = {}) => ({
  ...(f.operator ? { operator: f.operator } : {}), ...(f.days ? { days: f.days } : {}), include_sample: f.includeSample, tz_offset_min: tz(), ...extra,
});

export const useSummary = (f: AnalyticsFilters) =>
  useQuery({ queryKey: ["an-summary", f.operator, f.includeSample], queryFn: async () => (await api.get<Summary>("/api/analytics/summary", { params: { ...(f.operator ? { operator: f.operator } : {}), include_sample: f.includeSample } })).data, refetchInterval: 30_000 });
const dayKey = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

/** The API returns only days with activity; fill the calendar so gaps show as gaps. */
function fillDays(rows: TrendDay[], days: number | null): TrendDay[] {
  const today = new Date();
  const first = days ? new Date(today.getFullYear(), today.getMonth(), today.getDate() - days + 1) : rows[0] ? new Date(`${rows[0].day}T00:00:00`) : today;
  const byDay = new Map(rows.map((r) => [r.day, r]));
  const out: TrendDay[] = [];
  for (let d = first; dayKey(d) <= dayKey(today); d = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1)) {
    const k = dayKey(d);
    out.push(byDay.get(k) ?? { day: k, readings: 0, strong: 0, weak: 0, dead: 0, weak_share: null, dead_share: null, registered: 0, resolved: 0 });
  }
  return out;
}

export const useTrends = (f: AnalyticsFilters) =>
  useQuery({
    queryKey: ["an-trends", f],
    queryFn: async () => fillDays((await api.get<{ days: TrendDay[] }>("/api/analytics/trends", { params: params(f, { days: f.days ?? 3650 }) })).data.days, f.days),
  });
export const useWorst = (f: AnalyticsFilters) =>
  useQuery({ queryKey: ["an-worst", f], queryFn: async () => (await api.get<WorstArea[]>("/api/analytics/worst-areas", { params: params(f, { min_readings: 15, limit: 10 }) })).data });
export const useTimeOfDay = (f: AnalyticsFilters) =>
  useQuery({ queryKey: ["an-tod", f], queryFn: async () => (await api.get<{ cells: TodCell[] }>("/api/analytics/time-of-day", { params: params(f) })).data.cells });
export const useOperators = (f: AnalyticsFilters) =>
  useQuery({ queryKey: ["an-ops", f.days, f.includeSample], queryFn: async () => (await api.get<OperatorRow[]>("/api/analytics/operators", { params: { ...(f.days ? { days: f.days } : {}), include_sample: f.includeSample } })).data });
export const useFunnel = (f: AnalyticsFilters) =>
  useQuery({ queryKey: ["an-funnel", f.operator, f.includeSample], queryFn: async () => (await api.get<Funnel>("/api/analytics/complaint-funnel", { params: { ...(f.operator ? { operator: f.operator } : {}), include_sample: f.includeSample } })).data });

export function hoursText(h: number | null | undefined): string {
  if (h == null) return "–";
  if (h < 1) return `${Math.round(h * 60)} min`;
  if (h < 48) return `${h.toFixed(1)} h`;
  return `${(h / 24).toFixed(1)} days`;
}

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  CitizenComplaint,
  ComplaintDetail,
  Hotspots,
  Meta,
  ModelInfo,
  PublicStats,
  QueueResponse,
  SlaRow,
  Summary,
  Trends,
} from "@/lib/types";

/** Dashboards re-read the API this often so new complaints show up without a reload. */
export const LIVE_MS = 20_000;

export const keys = {
  meta: ["meta"] as const,
  publicStats: ["public-stats"] as const,
  mine: ["complaints", "mine"] as const,
  track: (id: string) => ["complaints", "track", id] as const,
  queue: (p: object) => ["queue", p] as const,
  detail: (id: number | string) => ["complaint", String(id)] as const,
  summary: ["analytics", "summary"] as const,
  hotspots: (days: number, category: string) => ["analytics", "hotspots", days, category] as const,
  sla: ["analytics", "sla"] as const,
  trends: ["analytics", "trends"] as const,
  model: ["model", "metrics"] as const,
};

export const useMeta = () =>
  useQuery({ queryKey: keys.meta, queryFn: async () => (await api.get<Meta>("/meta")).data, staleTime: 5 * 60_000 });

export const usePublicStats = () =>
  useQuery({
    queryKey: keys.publicStats,
    queryFn: async () => (await api.get<PublicStats>("/public/stats")).data,
    staleTime: 10 * 60_000,
    retry: false,
  });

export const useMyComplaints = () =>
  useQuery({
    queryKey: keys.mine,
    queryFn: async () => (await api.get<CitizenComplaint[]>("/complaints/mine")).data,
    refetchInterval: LIVE_MS,
  });

export const useTracked = (trackingId: string | undefined) =>
  useQuery({
    queryKey: keys.track(trackingId ?? ""),
    queryFn: async () => (await api.get<CitizenComplaint>(`/complaints/track/${encodeURIComponent(trackingId!)}`)).data,
    enabled: !!trackingId,
    refetchInterval: LIVE_MS,
    retry: false,
  });

export const useQueue = (params: { status: string; department: string; priority: string; q: string }) =>
  useQuery({
    queryKey: keys.queue(params),
    queryFn: async () => (await api.get<QueueResponse>("/officer/queue", { params })).data,
    refetchInterval: LIVE_MS,
    placeholderData: keepPreviousData,
  });

export const useComplaint = (id: string | undefined) =>
  useQuery({
    queryKey: keys.detail(id ?? ""),
    queryFn: async () => (await api.get<ComplaintDetail>(`/complaints/${id}`)).data,
    enabled: !!id,
    // poll while the Gemini extraction is still running
    refetchInterval: (q) => (q.state.data?.extraction_status === "pending" ? 2500 : false),
  });

export const useSummary = () =>
  useQuery({ queryKey: keys.summary, queryFn: async () => (await api.get<Summary>("/analytics/summary")).data, refetchInterval: LIVE_MS });

export const useHotspots = (days: number, category: string) =>
  useQuery({
    queryKey: keys.hotspots(days, category),
    queryFn: async () => (await api.get<Hotspots>("/analytics/hotspots", { params: { days, category } })).data,
    refetchInterval: LIVE_MS,
    placeholderData: keepPreviousData,
  });

export const useSla = () =>
  useQuery({ queryKey: keys.sla, queryFn: async () => (await api.get<SlaRow[]>("/analytics/sla")).data, refetchInterval: LIVE_MS });

export const useTrends = () =>
  useQuery({
    queryKey: keys.trends,
    queryFn: async () => (await api.get<Trends>("/analytics/trends", { params: { weeks: 12 } })).data,
    refetchInterval: LIVE_MS,
  });

export const useModelInfo = () =>
  useQuery({ queryKey: keys.model, queryFn: async () => (await api.get<ModelInfo>("/model/metrics")).data });

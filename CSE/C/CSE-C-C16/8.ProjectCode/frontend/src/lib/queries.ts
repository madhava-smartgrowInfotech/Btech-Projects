import { useQuery } from "@tanstack/react-query";

import {
  api,
  type AnalyticsData,
  type DashboardData,
  type Disease,
  type Health,
  type HistoryPage,
  type ResultDetail,
} from "@/lib/api";

export const keys = {
  health: ["health"] as const,
  diseases: ["diseases"] as const,
  disease: (c: string) => ["disease", c] as const,
  dashboard: ["dashboard"] as const,
  analytics: ["analytics"] as const,
  history: (p: object) => ["history", p] as const,
  result: (id: string) => ["result", id] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    queryFn: async () => (await api.get<Health>("/health")).data,
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useDiseases() {
  return useQuery({
    queryKey: keys.diseases,
    queryFn: async () => (await api.get<Disease[]>("/v1/diseases")).data,
    staleTime: 10 * 60_000,
  });
}

export function useDisease(cls: string | undefined) {
  return useQuery({
    queryKey: keys.disease(cls ?? ""),
    queryFn: async () => (await api.get<Disease>(`/v1/diseases/${encodeURIComponent(cls ?? "")}`)).data,
    enabled: Boolean(cls),
    retry: false,
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: keys.dashboard,
    queryFn: async () => (await api.get<DashboardData>("/v1/dashboard")).data,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: keys.analytics,
    queryFn: async () => (await api.get<AnalyticsData>("/v1/analytics/dashboard")).data,
  });
}

export interface HistoryParams {
  q: string;
  crop: string;
  disease: string;
  limit: number;
  offset: number;
}

export function useHistory(params: HistoryParams) {
  return useQuery({
    queryKey: keys.history(params),
    queryFn: async () => (await api.get<HistoryPage>("/v1/history", { params })).data,
    placeholderData: (prev) => prev,
  });
}

export function useResult(id: string | undefined) {
  return useQuery({
    queryKey: keys.result(id ?? ""),
    queryFn: async () => (await api.get<ResultDetail>(`/v1/history/${id}`)).data,
    enabled: Boolean(id),
    retry: false,
  });
}

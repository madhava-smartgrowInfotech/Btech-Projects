import { useQuery, useQueryClient, keepPreviousData } from "@tanstack/react-query";

import {
  api,
  type Analytics,
  type BudgetStatus,
  type Dashboard,
  type Goal,
  type Meta,
  type Notice,
  type Portfolio,
  type Showcase,
  type TransactionList,
} from "@/lib/api";

export const keys = {
  health: ["health"] as const,
  meta: ["meta"] as const,
  dashboard: ["dashboard"] as const,
  transactions: (p: object) => ["transactions", p] as const,
  analytics: (p: object) => ["analytics", p] as const,
  budgets: (m: number, y: number) => ["budgets", m, y] as const,
  goals: ["goals"] as const,
  investments: ["investments"] as const,
  insights: ["insights"] as const,
  notifications: ["notifications"] as const,
};

/** Everything that depends on the user's records: call after any create / update / delete. */
export function useRefreshData() {
  const qc = useQueryClient();
  return () =>
    Promise.all(
      ["dashboard", "transactions", "analytics", "budgets", "goals", "investments", "insights", "notifications", "meta"].map((k) =>
        qc.invalidateQueries({ queryKey: [k] }),
      ),
    );
}

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    queryFn: async () => (await api.get<{ status: string; ai_llm_enabled: boolean }>("/health")).data,
    refetchInterval: 30_000,
    retry: false,
  });
}

export function useMeta() {
  return useQuery({ queryKey: keys.meta, queryFn: async () => (await api.get<Meta>("/meta")).data, staleTime: 60_000 });
}

export function useDashboard() {
  return useQuery({ queryKey: keys.dashboard, queryFn: async () => (await api.get<Dashboard>("/dashboard")).data });
}

export interface TxnFilters {
  start?: string;
  end?: string;
  category?: string;
  type?: string;
  q?: string;
  sort?: string;
  order?: string;
}

export function useTransactions(filters: TxnFilters) {
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v && v !== "All"));
  return useQuery({
    queryKey: keys.transactions(params),
    queryFn: async () => (await api.get<TransactionList>("/transactions", { params })).data,
    placeholderData: keepPreviousData,
  });
}

export function useAnalytics(params: { start: string; end: string; type: string }) {
  return useQuery({
    queryKey: keys.analytics(params),
    queryFn: async () => (await api.get<Analytics>("/analytics", { params })).data,
    placeholderData: keepPreviousData,
  });
}

export function useBudgets(month: number, year: number) {
  return useQuery({
    queryKey: keys.budgets(month, year),
    queryFn: async () => (await api.get<{ items: BudgetStatus[]; month_name: string }>("/budgets", { params: { month, year } })).data,
    placeholderData: keepPreviousData,
  });
}

export function useGoals() {
  return useQuery({ queryKey: keys.goals, queryFn: async () => (await api.get<{ items: Goal[] }>("/goals")).data });
}

export function useInvestments() {
  return useQuery({ queryKey: keys.investments, queryFn: async () => (await api.get<Portfolio>("/investments")).data });
}

export function useInsights() {
  return useQuery({
    queryKey: keys.insights,
    queryFn: async () => (await api.get<{ insights: string[]; disclaimer: string; llm_enabled: boolean }>("/assistant/insights")).data,
  });
}

export function useNotifications(options?: { poll?: boolean }) {
  return useQuery({
    queryKey: keys.notifications,
    queryFn: async () => (await api.get<{ items: Notice[]; unread: number }>("/notifications")).data,
    refetchInterval: options?.poll ? 60_000 : false,
  });
}

export function useShowcase() {
  return useQuery({
    queryKey: ["showcase"],
    queryFn: async () => (await api.get<Showcase>("/public/showcase")).data,
    staleTime: 5 * 60_000,
    retry: false,
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  ClaimCase,
  Clause,
  Comparison,
  Conversation,
  ConversationDetail,
  DashboardSummary,
  Exchange,
  Language,
  PageInfo,
  Policy,
  PolicyCardResponse,
  Risk,
  SearchResponse,
} from "@/lib/types";

const PROCESSING = new Set(["queued", "parsing", "indexing", "extracting"]);

export const keys = {
  policies: ["policies"] as const,
  policy: (id: number) => ["policies", id] as const,
  card: (id: number, lang: string) => ["policies", id, "card", lang] as const,
  risks: (id: number, lang: string) => ["policies", id, "risks", lang] as const,
  pages: (id: number) => ["policies", id, "pages"] as const,
  clauses: (id: number) => ["policies", id, "clauses"] as const,
  conversations: ["conversations"] as const,
  conversation: (id: number) => ["conversations", id] as const,
  claims: ["claims"] as const,
  claim: (id: number) => ["claims", id] as const,
  comparisons: ["comparisons"] as const,
  comparison: (id: number) => ["comparisons", id] as const,
  dashboard: ["dashboard"] as const,
  evaluation: ["evaluation", "latest"] as const,
};

export function usePolicies() {
  return useQuery({
    queryKey: keys.policies,
    queryFn: async () => (await api.get<Policy[]>("/policies")).data,
    refetchInterval: (query) =>
      (query.state.data ?? []).some((p) => PROCESSING.has(p.document.status)) ? 2500 : false,
  });
}

export function usePolicy(id: number) {
  return useQuery({
    queryKey: keys.policy(id),
    queryFn: async () => (await api.get<Policy>(`/policies/${id}`)).data,
    enabled: Number.isFinite(id),
    refetchInterval: (query) => (query.state.data && PROCESSING.has(query.state.data.document.status) ? 2000 : false),
  });
}

export function usePolicyCard(id: number, lang: Language, enabled = true) {
  return useQuery({
    queryKey: keys.card(id, lang),
    queryFn: async () => (await api.get<PolicyCardResponse>(`/policies/${id}/card`, { params: { lang } })).data,
    enabled: enabled && Number.isFinite(id),
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function useRisks(id: number, lang: Language, enabled = true) {
  return useQuery({
    queryKey: keys.risks(id, lang),
    queryFn: async () => (await api.get<Risk[]>(`/policies/${id}/risks`, { params: { lang } })).data,
    enabled: enabled && Number.isFinite(id),
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function usePages(id: number, enabled = true) {
  return useQuery({
    queryKey: keys.pages(id),
    queryFn: async () => (await api.get<PageInfo[]>(`/policies/${id}/pages`)).data,
    enabled: enabled && Number.isFinite(id),
    staleTime: Infinity,
  });
}

export function useClauses(id: number, enabled = true) {
  return useQuery({
    queryKey: keys.clauses(id),
    queryFn: async () => (await api.get<Clause[]>(`/policies/${id}/clauses`)).data,
    enabled: enabled && Number.isFinite(id),
    staleTime: Infinity,
  });
}

export function useUploadPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, name, onProgress }: { file: File; name?: string; onProgress?: (p: number) => void }) => {
      const form = new FormData();
      form.append("file", file);
      if (name) form.append("display_name", name);
      const res = await api.post<Policy>("/policies", form, {
        onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded / e.total) * 100)),
      });
      return res.data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.policies }),
  });
}

export function useAddSamples() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<Policy[]>("/policies/samples")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.policies }),
  });
}

export function useDeletePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => api.delete(`/policies/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.policies });
      qc.invalidateQueries({ queryKey: keys.conversations });
      qc.invalidateQueries({ queryKey: keys.dashboard });
    },
  });
}

export function useReextract(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post(`/policies/${id}/extract`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.policy(id) }),
  });
}

export function useClauseSearch(id: number) {
  return useMutation({
    mutationFn: async (body: { query: string; mode: string; k?: number }) =>
      (await api.post<SearchResponse>(`/policies/${id}/search`, body)).data,
  });
}

export function useConversations() {
  return useQuery({
    queryKey: keys.conversations,
    queryFn: async () => (await api.get<Conversation[]>("/conversations")).data,
  });
}

export function useConversation(id: number | null) {
  return useQuery({
    queryKey: keys.conversation(id ?? -1),
    queryFn: async () => (await api.get<ConversationDetail>(`/conversations/${id}`)).data,
    enabled: id !== null && Number.isFinite(id),
  });
}

export function useCreateConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (policyId: number) =>
      (await api.post<Conversation>("/conversations", { policy_id: policyId })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.conversations }),
  });
}

export function useDeleteConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => api.delete(`/conversations/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.conversations }),
  });
}

export function useAsk(conversationId: number | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ question, language }: { question: string; language: Language }) =>
      (await api.post<Exchange>(`/conversations/${conversationId}/messages`, { question, language })).data,
    onSuccess: (data) => {
      qc.setQueryData<ConversationDetail>(keys.conversation(conversationId ?? -1), (old) =>
        old ? { ...old, messages: [...old.messages, data.question, data.answer] } : old,
      );
      qc.invalidateQueries({ queryKey: keys.conversations });
      qc.invalidateQueries({ queryKey: keys.dashboard });
    },
  });
}

export function useClaims() {
  return useQuery({ queryKey: keys.claims, queryFn: async () => (await api.get<ClaimCase[]>("/claims")).data });
}

export function useClaim(id: number | null) {
  return useQuery({
    queryKey: keys.claim(id ?? -1),
    queryFn: async () => (await api.get<ClaimCase>(`/claims/${id}`)).data,
    enabled: id !== null && Number.isFinite(id),
  });
}

export function useCreateClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => (await api.post<ClaimCase>("/claims", body)).data,
    onSuccess: (data) => {
      qc.setQueryData(keys.claim(data.id), data);
      qc.invalidateQueries({ queryKey: keys.claims });
      qc.invalidateQueries({ queryKey: keys.dashboard });
    },
  });
}

export function useToggleChecklist(caseId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ itemId, done }: { itemId: string; done: boolean }) =>
      (await api.patch<ClaimCase>(`/claims/${caseId}/checklist`, { item_id: itemId, done })).data,
    onMutate: async ({ itemId, done }) => {
      qc.setQueryData<ClaimCase>(keys.claim(caseId), (old) =>
        old ? { ...old, checklist_state: { ...old.checklist_state, [itemId]: done } } : old,
      );
    },
    onSuccess: (data) => qc.setQueryData(keys.claim(caseId), data),
  });
}

export function useDeleteClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => api.delete(`/claims/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.claims }),
  });
}

export function useComparisons() {
  return useQuery({
    queryKey: keys.comparisons,
    queryFn: async () => (await api.get<Comparison[]>("/comparisons")).data,
  });
}

export function useComparison(id: number | null) {
  return useQuery({
    queryKey: keys.comparison(id ?? -1),
    queryFn: async () => (await api.get<Comparison>(`/comparisons/${id}`)).data,
    enabled: id !== null && Number.isFinite(id),
  });
}

export function useCreateComparison() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { policy_a_id: number; policy_b_id: number; language: Language }) =>
      (await api.post<Comparison>("/comparisons", body)).data,
    onSuccess: (data) => {
      qc.setQueryData(keys.comparison(data.id), data);
      qc.invalidateQueries({ queryKey: keys.comparisons });
    },
  });
}

export function useDeleteComparison() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => api.delete(`/comparisons/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.comparisons }),
  });
}

export function useDashboard() {
  return useQuery({
    queryKey: keys.dashboard,
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
  });
}

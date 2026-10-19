import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  AdminOverview, AuditorOverview, BenchmarkRun, BlockDetail, Candidate, ChainStatus, Election, ElectionDetail,
  ElectionStats, PublicOverview, Receipt, TallyResult, TamperResult, VerifyResult, VoterElection, VoterElectionDetail,
} from "@/lib/types";

export const keys = {
  public: ["public"] as const,
  admin: ["admin", "overview"] as const,
  elections: ["admin", "elections"] as const,
  election: (id: number) => ["admin", "election", id] as const,
  benchmarks: ["admin", "benchmarks"] as const,
  results: (id: number) => ["results", id] as const,
  voterElections: ["voter", "elections"] as const,
  voterElection: (id: number) => ["voter", "election", id] as const,
  auditor: ["auditor", "overview"] as const,
  block: (i: number) => ["auditor", "block", i] as const,
};

export const usePublicOverview = () =>
  useQuery({ queryKey: keys.public, queryFn: async () => (await api.get<PublicOverview>("/public/overview")).data });

export const useAdminOverview = () =>
  useQuery({ queryKey: keys.admin, queryFn: async () => (await api.get<AdminOverview>("/admin/overview")).data });

export const useAdminElections = () =>
  useQuery({
    queryKey: keys.elections,
    queryFn: async () => (await api.get<{ elections: ElectionStats[] }>("/admin/elections")).data.elections,
  });

export const useAdminElection = (id: number) =>
  useQuery({ queryKey: keys.election(id), queryFn: async () => (await api.get<ElectionDetail>(`/admin/elections/${id}`)).data });

export const useBenchmarks = () =>
  useQuery({
    queryKey: keys.benchmarks,
    queryFn: async () => (await api.get<{ runs: BenchmarkRun[] }>("/admin/benchmarks")).data.runs,
  });

export const useResults = (id: number) =>
  useQuery({
    queryKey: keys.results(id),
    queryFn: async () => (await api.get<{ election: Election } & TallyResult>(`/elections/${id}/results`)).data,
    retry: false,
  });

export const useVoterElections = () =>
  useQuery({
    queryKey: keys.voterElections,
    queryFn: async () => (await api.get<{ elections: VoterElection[] }>("/voter/elections")).data.elections,
  });

export const useVoterElection = (id: number) =>
  useQuery({
    queryKey: keys.voterElection(id),
    queryFn: async () => (await api.get<VoterElectionDetail>(`/voter/elections/${id}`)).data,
  });

export const useAuditorOverview = () =>
  useQuery({ queryKey: keys.auditor, queryFn: async () => (await api.get<AuditorOverview>("/auditor/overview")).data });

export const useBlock = (index: number) =>
  useQuery({
    queryKey: keys.block(index),
    queryFn: async () => (await api.get<BlockDetail>(`/auditor/blocks/${index}`)).data,
    retry: false,
  });

/* ---- mutations ---- */
export function useCreateElection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { title: string; description: string; start_time: string; end_time: string }) =>
      (await api.post<Election>("/admin/elections", body)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin"] });
      qc.invalidateQueries({ queryKey: keys.public });
    },
  });
}

export function useSetStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) =>
      (await api.post<Election>(`/admin/elections/${id}/status`, { status })).data,
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ["admin"] });
      qc.invalidateQueries({ queryKey: ["voter"] });
      qc.invalidateQueries({ queryKey: keys.results(v.id) });
      qc.invalidateQueries({ queryKey: keys.public });
    },
  });
}

export function useAddCandidate(electionId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { name: string; party: string; description: string; manifesto: string }) =>
      (await api.post<Candidate>(`/admin/elections/${electionId}/candidates`, body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export function useToggleCandidate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (cid: number) => (await api.post<Candidate>(`/admin/candidates/${cid}/toggle`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin"] }),
  });
}

export function useVerifyAadhaar(electionId: number) {
  return useMutation({
    mutationFn: async (aadhaar: string) =>
      (await api.post<VerifyResult>(`/voter/elections/${electionId}/verify`, { aadhaar })).data,
  });
}

export function useCastVote(electionId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { candidate_id: number; auth_token: string }) =>
      (await api.post<{ election: Election; receipt: Receipt }>(`/voter/elections/${electionId}/cast`, body)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["voter"] });
      qc.invalidateQueries({ queryKey: ["auditor"] });
      qc.invalidateQueries({ queryKey: ["admin"] });
      qc.invalidateQueries({ queryKey: keys.public });
    },
  });
}

export function useVerifyChain() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<ChainStatus>("/auditor/verify")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.auditor }),
  });
}

export function useTamperTest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<TamperResult>("/auditor/tamper-test")).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.auditor }),
  });
}

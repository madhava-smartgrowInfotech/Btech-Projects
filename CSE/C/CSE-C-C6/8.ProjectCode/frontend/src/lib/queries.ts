import { useQuery } from "@tanstack/react-query";

import { api, type ModelInfo, type Sample } from "@/lib/api";

export const keys = {
  model: ["model"] as const,
  samples: ["samples"] as const,
  health: ["health"] as const,
};

export function useModel() {
  return useQuery({
    queryKey: keys.model,
    queryFn: async () => (await api.get<ModelInfo>("/model")).data,
    staleTime: 60_000,
  });
}

export function useSamples() {
  return useQuery({
    queryKey: keys.samples,
    queryFn: async () => (await api.get<{ samples: Sample[] }>("/samples")).data.samples,
    staleTime: Infinity,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    queryFn: async () => (await api.get<{ status: string }>("/health")).data,
    refetchInterval: 20_000,
    retry: false,
  });
}

import { useQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api";

export const keys = {
  health: ["health"] as const,
  config: ["config"] as const,
  about: ["about"] as const,
  dataset: ["dataset"] as const,
  images: (cls: string) => ["images", cls] as const,
  model: ["model"] as const,
  train: ["train-status"] as const,
};

export const useHealth = () =>
  useQuery({ queryKey: keys.health, queryFn: endpoints.health, refetchInterval: 8000, staleTime: 4000, retry: 0 });

export const useConfig = () => useQuery({ queryKey: keys.config, queryFn: endpoints.config, staleTime: Infinity });

export const useAbout = () => useQuery({ queryKey: keys.about, queryFn: endpoints.about, staleTime: Infinity });

export const useDataset = () => useQuery({ queryKey: keys.dataset, queryFn: endpoints.dataset, staleTime: 3000 });

export const useImages = (cls: string, limit = 24) =>
  useQuery({ queryKey: [...keys.images(cls), limit], queryFn: () => endpoints.images(cls, limit), staleTime: 2000 });

/** `null` data (not an error) when no model has been trained yet. */
export const useModel = () =>
  useQuery({
    queryKey: keys.model,
    queryFn: async () => {
      const info = await endpoints.model();
      return info.trained ? info : null;
    },
    staleTime: 5000,
  });

export const useTrainStatus = () =>
  useQuery({
    queryKey: keys.train,
    queryFn: endpoints.trainStatus,
    refetchInterval: (q) => (q.state.data && (q.state.data.state === "loading" || q.state.data.state === "training") ? 1000 : false),
  });

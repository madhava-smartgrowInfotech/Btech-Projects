import { useQuery } from "@tanstack/react-query";

import { endpoints } from "@/lib/api";

export const keys = {
  health: ["health"] as const,
  config: ["config"] as const,
  about: ["about"] as const,
  settings: ["settings"] as const,
  history: ["history"] as const,
  research: ["research"] as const,
};

export const useHealth = () =>
  useQuery({ queryKey: keys.health, queryFn: endpoints.health, refetchInterval: 10_000, staleTime: 5000, retry: 0 });

export const useConfig = () => useQuery({ queryKey: keys.config, queryFn: endpoints.config, staleTime: Infinity });

export const useAbout = () => useQuery({ queryKey: keys.about, queryFn: endpoints.about, staleTime: Infinity });

export const useSettings = () => useQuery({ queryKey: keys.settings, queryFn: endpoints.settings, staleTime: 0 });

export const useHistory = () => useQuery({ queryKey: keys.history, queryFn: () => endpoints.history(500), staleTime: 0 });

export const useResearch = () => useQuery({ queryKey: keys.research, queryFn: endpoints.research, staleTime: 0 });

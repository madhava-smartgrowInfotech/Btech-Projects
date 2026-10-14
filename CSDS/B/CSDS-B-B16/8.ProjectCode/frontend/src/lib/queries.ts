// React Query keys. Mutations invalidate by the first segment (e.g. ["patients"]).
export const keys = {
  patients: (q: string) => ["patients", q] as const,
  patient: (id: string) => ["patient", id] as const,
  recentScreenings: ["screenings", "recent"] as const,
  screening: (id: string) => ["screening", id] as const,
  samples: ["samples"] as const,
  metrics: ["metrics"] as const,
};

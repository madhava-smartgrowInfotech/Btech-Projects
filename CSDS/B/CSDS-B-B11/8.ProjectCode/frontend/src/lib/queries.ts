// React Query keys in one place, so screens can refresh each other's data after a change.
export const keys = {
  evaluation: ["evaluation"] as const,
  profileOptions: ["profile", "options"] as const,
  profile: ["profile"] as const,
  targets: ["targets"] as const,
  plan: ["plan", "latest"] as const,
  logs: (date: string) => ["logs", date] as const,
  progress: (days: number) => ["progress", days] as const,
  usda: (q: string) => ["usda", q] as const,
  search: (q: string) => ["foods", "search", q] as const,
};

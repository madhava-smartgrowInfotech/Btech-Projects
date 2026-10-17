/** React Query keys, in one place so mutations can invalidate the right screens. */
export const keys = {
  me: ["me"] as const,
  dashboard: ["dashboard"] as const,
  documents: ["documents"] as const,
  history: ["ask-history"] as const,
  roadmap: ["roadmap"] as const,
  health: ["health"] as const,
};

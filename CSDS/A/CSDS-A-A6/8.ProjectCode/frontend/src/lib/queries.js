// React Query keys. Keeping them in one place lets uploads invalidate the list and reports.
export const keys = {
  contracts: ["contracts"],
  contract: (id) => ["contracts", id],
  clause: (id, clauseId) => ["contracts", id, "clauses", clauseId],
  graph: (id) => ["contracts", id, "graph"],
  evaluation: ["evaluation", "metrics"],
};

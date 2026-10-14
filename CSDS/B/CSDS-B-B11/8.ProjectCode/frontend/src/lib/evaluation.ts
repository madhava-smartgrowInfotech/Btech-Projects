import { keys } from "@/lib/queries";
import api from "@/lib/api";
import type { EvaluationResponse } from "@/lib/types";

/** Measured results from ml/eval.py (GET /api/evaluation). Shared by the landing page sections. */
export const evaluationQuery = {
  queryKey: keys.evaluation,
  queryFn: async () => (await api.get<EvaluationResponse>("/evaluation")).data,
  retry: false,
  staleTime: 10 * 60_000,
};

/** "peanut" / "north_indian" -> "Peanut" / "North indian" */
export function label(value: string): string {
  const s = value.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export const fmt = (n: number) => Math.round(n).toLocaleString("en-IN");

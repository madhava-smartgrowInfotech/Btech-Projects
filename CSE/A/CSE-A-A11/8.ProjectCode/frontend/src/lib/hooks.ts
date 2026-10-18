import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { Meta, Review, ReviewRow, Samples } from "@/lib/types";

export const useMeta = () =>
  useQuery({ queryKey: keys.meta, queryFn: async () => (await api.get<Meta>("/meta")).data, staleTime: 10 * 60_000 });

export const useSamples = (enabled = true) =>
  useQuery({ queryKey: keys.samples, queryFn: async () => (await api.get<Samples>("/samples")).data, staleTime: Infinity, enabled });

export const useReviews = () =>
  useQuery({ queryKey: keys.reviews, queryFn: async () => (await api.get<ReviewRow[]>("/reviews", { params: { limit: 200 } })).data });

export const useReview = (id: string | undefined) =>
  useQuery({
    queryKey: keys.review(id ?? ""),
    queryFn: async () => (await api.get<Review>(`/reviews/${id}`)).data,
    enabled: Boolean(id),
    staleTime: 5 * 60_000,
  });

/** Starts a review job on the API and returns its id (poll it with useJob). */
export async function startReview(body: Record<string, unknown>): Promise<string> {
  return (await api.post<{ job_id: string }>("/reviews", body)).data.job_id;
}

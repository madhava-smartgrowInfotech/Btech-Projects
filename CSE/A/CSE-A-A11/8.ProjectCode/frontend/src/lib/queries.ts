export const keys = {
  stats: ["public-stats"] as const,
  example: ["public-example"] as const,
  meta: ["meta"] as const,
  samples: ["samples"] as const,
  reviews: ["reviews"] as const,
  review: (id: string) => ["review", id] as const,
  lab: ["lab-report"] as const,
  markdown: (id: string) => ["review-md", id] as const,
};

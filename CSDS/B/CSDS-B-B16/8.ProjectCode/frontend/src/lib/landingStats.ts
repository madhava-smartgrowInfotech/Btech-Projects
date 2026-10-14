// Figures for the public landing page. The app does not expose /api/metrics without sign-in, so the
// landing page shows these fixed values instead. They come from experiments/eval/metrics.json
// (evaluated 2026-09-28) and match the README evaluation table. Update them if ml/eval.py is re-run.
export const LANDING_STATS = {
  source: "experiments/eval/metrics.json, evaluated 2026-09-28",
  retina: { testCases: 107, rocAuc: 0.7247, sensitivity: 0.6591 },
  heart: { testCases: 76, rocAuc: 0.885, sensitivity: 0.8, cvRocAuc: 0.9176 },
  dataset: { retinaImages: 712, heartPatients: 302 },
} as const;

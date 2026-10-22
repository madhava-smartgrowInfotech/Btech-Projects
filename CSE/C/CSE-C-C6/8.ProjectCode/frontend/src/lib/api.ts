import axios from "axios";

/** All calls go through the Vite proxy (/api -> backend), so no CORS and no hard-coded port. */
export const api = axios.create({ baseURL: "/api", timeout: 120_000 });

/** Turns any thrown value into a sentence for the user (API detail first, then a network hint). */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail) return detail;
    if (Array.isArray(detail) && detail.length) return detail.map((d) => d?.msg ?? String(d)).join("; ");
    // no response at all, or the dev proxy answering for a backend that is down
    if (!error.response || [502, 503, 504].includes(error.response.status))
      return "Can't reach the detection API. Start the backend (run.bat) and try again.";
    return `The server answered ${error.response.status}.`;
  }
  return error instanceof Error ? error.message : "Something went wrong.";
}

export const LABELS = ["REAL", "PARTIALLY TRUE", "FAKE"] as const;
export type Label = (typeof LABELS)[number];

export interface Prediction {
  label: Label;
  label_id: number;
  confidence: number | null;
  probabilities: Record<Label, number> | null;
  latency_ms: number;
  word_count: number;
  cues: { sensational: string[]; credibility: string[] };
}

export interface ClassReportRow {
  precision: number;
  recall: number;
  "f1-score": number;
  support: number;
}

export interface ModelStats {
  n_docs: number;
  n_tfidf: number;
  n_total_features: number;
  n_pca: number;
  pca_variance: number;
  n_selected: number;
  best_C: number;
  best_gamma: number;
  firefly_history: number[];
  accuracy: number;
  f1_macro: number;
  report: Record<string, ClassReportRow | number>;
  report_str: string;
  confusion_matrix: number[][];
  baseline_accuracy: number;
  baseline_f1: number;
  train_time_s: number;
  baseline_time_s: number;
}

export interface ModelInfo {
  labels: Label[];
  stats: ModelStats;
  pipeline: { title: string; text: string }[];
}

export interface Sample {
  label: Label;
  text: string;
}

export interface BatchPreview {
  filename: string;
  n_rows: number;
  columns: string[];
  guessed_column: string;
  preview: Record<string, string>[];
}

export interface BatchRow {
  row: number;
  text: string;
  predicted: Label;
  confidence: number | null;
}

export interface BatchResult {
  filename: string;
  column: string;
  n_rows: number;
  seconds: number;
  rows: BatchRow[];
  distribution: Record<Label, number>;
  csv: string;
}

export interface RetrainStatus {
  status: "running" | "done" | "error";
  elapsed_s: number;
  source: string;
  settings: { fireflies: number; generations: number; max_tfidf: number };
  result?: { accuracy: number; f1_macro: number; n_docs: number; n_selected: number; n_pca: number; train_time_s: number };
  error?: string;
}

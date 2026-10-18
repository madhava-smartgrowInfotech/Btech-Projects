export interface Health {
  status: string;
  product: string;
  model_loaded: boolean;
  model_file: boolean;
  training_state: TrainState;
}

export interface AppConfig {
  classes: string[];
  letter_classes: string[];
  control_classes: string[];
  frame: { width: number; height: number };
  roi: { x1: number; y1: number; x2: number; y2: number };
  img_size: number;
  segmentation_mode: string;
  thresholds: { confidence: number; history_len: number; stable_frames: number };
  capture_delay_ms: number;
  training_defaults: {
    epochs: number;
    batch_size: number;
    learning_rate: number;
    validation_split: number;
    test_split: number;
  };
}

export interface About {
  title: string;
  batch: string;
  abstract: string;
  pipeline: string[];
  base_paper: Record<string, string>;
  adoption_note: string;
}

export interface DatasetSummary {
  counts: Record<string, number>;
  total: number;
  trainable_classes: string[];
  ready_to_train: boolean;
}

export interface ImageList {
  class: string;
  total: number;
  images: { name: string; url: string }[];
}

export interface CollectResult {
  class: string;
  saved: string;
  count: number;
  mask: string;
}

export interface RecognizeResult {
  label: string;
  confidence: number;
  stable_label: string;
  committed: string | null;
  mask: string;
}

export type TrainState = "idle" | "loading" | "training" | "done" | "error";

export interface TrainStatus {
  state: TrainState;
  data: { done: number; total: number };
  epoch: number;
  epochs: number;
  history: { accuracy: number[]; val_accuracy: number[]; loss: number[]; val_loss: number[] };
  summary: { labels: string[]; test_accuracy: number; test_loss: number } | null;
  error: string | null;
  stopping: boolean;
  started_at: number | null;
  finished_at: number | null;
}

export interface ReportRow {
  label: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface ModelInfo {
  trained: boolean;
  loaded: boolean;
  labels: string[];
  test_accuracy: number | null;
  test_loss: number | null;
  report: string;
  report_rows: ReportRow[];
  history: Record<string, number[]> | null;
  confusion_matrix: { labels: string[]; matrix: number[][] } | null;
  trained_at: number | null;
}

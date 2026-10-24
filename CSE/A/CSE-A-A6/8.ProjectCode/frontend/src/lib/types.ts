export interface Health {
  status: string;
  landmark_model: boolean;
  history_events: number;
  model_report: boolean;
}

export interface Bound {
  min: number;
  max: number;
  step: number;
  label: string;
  help: string;
}

export interface AppConfig {
  title: string;
  scenarios: string[];
  bounds: Record<string, Bound>;
  defaults: Record<string, number>;
  frame: { width: number; height: number };
  quality_gates: string[];
  disclaimers: string[];
  states: { normal: string; warning: string; unknown: string };
}

export interface About {
  title: string;
  summary: string;
  pipeline: { name: string; text: string }[];
  formulas: { name: string; text: string }[];
  rules: string[];
  limitations: string[];
  reference: { citation: string; doi: string; note: string };
  cli_tools: { name: string; text: string }[];
}

export interface Metrics {
  ear: number | null;
  closure: number | null;
  blink_rate: number | null;
  closed_fraction: number | null;
  roll: number | null;
}

export type Source = "none" | "camera" | "simulation";

export interface SessionState {
  session_id: string;
  source: Source;
  source_label: string;
  scenario: string;
  monitoring: boolean;
  calibrating: boolean;
  calibration: { progress: number; usable: number; attempts: number; elapsed: number } | null;
  status: string;
  quality: string;
  brightness: number;
  state: string;
  reason: string;
  alert: string;
  alert_seq: number;
  metrics: Metrics | null;
  threshold: number;
  calibrated: boolean;
  frames: number;
  verdicts: { normal: string; warning: string; unknown: string };
  preview?: string;
}

export interface SettingsPayload {
  settings: Record<string, number>;
  calibrated: boolean;
  note: string;
}

export interface HistoryEvent {
  id: number;
  timestamp: string;
  source: string;
  state: string;
  quality: string;
  reason: string;
  ear: number;
  closure: number;
  blink_rate: number;
  closed_fraction: number;
  roll: number;
  alert: boolean;
  simulation: boolean;
}

export interface HistoryPayload {
  events: HistoryEvent[];
  total: number;
  summary: { warnings: number; normal: number; unknown: number; alerts: number; simulation: number; live: number };
}

export interface ResearchReport {
  status: string;
  classifier: string;
  features: string[];
  confusion_matrix: number[][];
  matrix_order: string;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  false_alarm_rate: number | null;
  train_subjects: string[];
  test_subjects: string[];
  train_windows: number;
  test_windows: number;
  rejected_windows: number;
  dataset_sha256: string;
  limitation: string;
}

export interface ResearchPayload {
  trained: boolean;
  status: string;
  synthetic: boolean;
  report?: ResearchReport;
  files: string[];
  confusion_matrix_image?: boolean;
}

export interface AuthUser {
  email: string;
  name: string;
}

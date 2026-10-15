export type Role = "citizen" | "officer" | "admin";
export type Priority = "Low" | "Medium" | "High" | "Critical";
export type Status = "Submitted" | "Assigned" | "In Progress" | "Resolved" | "Rejected";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  department: string | null;
}

export interface Meta {
  categories: { name: string; department: string }[];
  departments: { id: number; name: string; sla_days: number }[];
  priorities: Priority[];
  wards: { name: string; lat: number; lng: number }[];
}

export interface TimelineEvent {
  kind: string;
  status: Status | null;
  message: string | null;
  at: string;
}

export interface CitizenComplaint {
  id: number;
  tracking_id: string;
  text: string;
  language: string;
  photo_url: string | null;
  lat: number | null;
  lng: number | null;
  ward: string | null;
  status: Status;
  created_at: string;
  resolved_at: string | null;
  department: string | null;
  expected_days: number | null;
  expected_by: string | null;
  timeline: TimelineEvent[];
  is_sample: boolean;
}

export interface CurrentView {
  category: string;
  department: string;
  priority: Priority;
  expected_days: number | null;
  expected_by: string | null;
  sla_days: number | null;
  sla_due: string | null;
  sla_breach_risk: boolean;
  sla_breached: boolean;
  age_days: number;
  decided: boolean;
}

export interface QueueItem {
  id: number;
  tracking_id: string;
  text: string;
  language: string;
  ward: string | null;
  status: Status;
  created_at: string;
  has_photo: boolean;
  is_sample: boolean;
  extraction_status: string;
  ai: {
    category: string;
    category_confidence: number;
    department: string;
    department_confidence: number;
    priority: Priority;
    priority_confidence: number;
    expected_days: number;
    sla_breach_risk: boolean;
  };
  top_words: string[];
  current: CurrentView;
}

export interface QueueResponse {
  items: QueueItem[];
  total: number;
  counts: Record<Status, number>;
}

export interface Alt {
  label: string;
  p: number;
}
export interface WordWeight {
  word: string;
  weight: number;
}
export interface Factor {
  factor: string;
  value: string | number;
  impact: number;
}
export interface Explanations {
  category_words?: WordWeight[];
  priority_factors?: { target: string; factors: Factor[] };
  time_factors?: { baseline_days: number; factors: Factor[] };
}

export interface Extraction {
  place?: string | null;
  issue?: string | null;
  affected_people?: string | null;
  duration?: string | null;
  hazards?: string[];
  summary_en?: string;
  error?: string;
}

export interface ComplaintDetail {
  id: number;
  tracking_id: string;
  text: string;
  language: string;
  photo_url: string | null;
  lat: number | null;
  lng: number | null;
  ward: string | null;
  status: Status;
  is_sample: boolean;
  created_at: string;
  resolved_at: string | null;
  citizen: string;
  ai: {
    category: string;
    category_confidence: number;
    category_top3?: Alt[];
    department: string;
    department_confidence: number;
    department_top3?: Alt[];
    priority: Priority;
    priority_confidence: number;
    priority_proba?: Record<string, number>;
    expected_days: number;
    model_version?: number;
    explained_with_version?: number;
    explanations?: Explanations;
  };
  extraction: Extraction | null;
  extraction_status: "pending" | "done" | "failed" | string;
  final: {
    category: string | null;
    department: string | null;
    priority: Priority | null;
    expected_days: number | null;
    reviewed_by: string | null;
    reviewed_at: string | null;
  };
  current: CurrentView;
  feedback: { field: string; ai_value: string; officer_value: string; action: string; reason: string; officer: string | null; at: string }[];
  events: { kind: string; status: Status | null; message: string | null; public: boolean; actor: string | null; at: string }[];
  statuses: Status[];
}

export interface Summary {
  total: number;
  open: number;
  awaiting_review: number;
  filed_last_24h: number;
  resolved_last_30d: number;
  sla_compliance: number | null;
  open_sla_breached: number;
  avg_resolution_days: number | null;
  time_estimate_mae_days: number | null;
  by_status: Record<string, number>;
  open_by_priority: Record<string, number>;
  by_language: Record<string, number>;
  ai_acceptance: Record<"category" | "department" | "priority", { reviewed: number; accepted: number; rate: number | null }>;
  updated_at: string;
}

export interface Hotspots {
  days: number;
  wards: { ward: string; lat: number; lng: number; total: number; open: number; critical_or_high: number; top_category: string; top_count: number }[];
  recurring: { ward: string; category: string; count: number; open: number }[];
  points: { id: number; tracking_id: string; lat: number; lng: number; category: string; priority: Priority; status: Status }[];
}

export interface SlaRow {
  department: string;
  sla_days: number;
  open: number;
  open_breached: number;
  resolved: number;
  within_sla: number;
  compliance: number | null;
  avg_days: number | null;
}

export interface Trends {
  weeks: string[];
  series: { category: string; counts: number[]; total: number }[];
}

interface TaskMetrics {
  test: { accuracy: number; macro_f1: number };
  by_language: Record<string, number>;
}
export interface ModelMetrics {
  version: number;
  category: TaskMetrics;
  department: TaskMetrics;
  priority: TaskMetrics;
  resolution?: {
    rows_test: number;
    mae_days: number;
    median_abs_error_days: number;
    baseline_category_median_mae_days?: number;
    baseline_category_median_median_abs_error_days?: number;
    sla_breach_flag_accuracy: number;
  };
  feedback: {
    labels_used: number;
    officer_agreement_before?: Record<string, number>;
    officer_agreement_after?: Record<string, number>;
  };
  train_seconds: number;
}
export interface ModelInfo {
  current: ModelMetrics | null;
  model_version: number;
  new_labels_since_last_run: number;
  total_officer_labels: number;
  runs: { version: number; labels_used: number; at: string }[];
}
export interface RetrainResult {
  before: ModelMetrics | null;
  after: ModelMetrics;
}

export interface PublicStats {
  available: boolean;
  model_version?: number;
  category?: { accuracy: number; n: number; by_language: Record<string, number> };
  department?: { accuracy: number; top3: number | null };
  priority?: { accuracy: number };
  resolution?: { median_abs_error_days: number; rows_test: number };
  explanations?: { lime_drop: number; random_drop: number };
  latency_ms?: number | null;
  agreement_after_feedback?: number | null;
}

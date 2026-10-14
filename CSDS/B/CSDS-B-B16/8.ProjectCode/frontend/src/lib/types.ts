// Response shapes of the RetinaGuard API (backend/app/routes). Field names match the JSON exactly.

export type Stage = "Low" | "Moderate" | "High" | "Very high";

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  role: string;
}

export interface LoginResponse {
  token: string;
  user: AuthUser;
}

export interface PatientSummary {
  id: number;
  code: string;
  name: string;
  age: number;
  sex: string;
  created_at: string;
  screening_count: number;
  latest_stage: Stage | null;
  last_screened: string | null;
}

export interface ScreeningSummary {
  id: number;
  patient_id: number;
  patient_name: string;
  patient_code: string;
  eye: string;
  created_at: string;
  retina_prob: number | null;
  heart_prob: number | null;
  stage: Stage | null;
  quality_passed: boolean | null;
  screened_by: string;
}

export interface PatientDetail extends PatientSummary {
  screenings: ScreeningSummary[];
}

export interface StageDetail {
  stage: Stage;
  score: number;
  reasons: string[];
  recommendations: string[];
}

export interface QualityReport {
  passed?: boolean;
  sharpness?: number;
  brightness?: number;
  clipped_fraction?: number;
  thresholds?: { sharpness_min?: number; brightness_range?: [number, number] };
  issues?: string[];
}

export interface VesselMetrics {
  vessel_density?: number;
  mean_vessel_width_px?: number;
}

export interface RetinaFindings {
  label?: string;
  positive?: boolean;
  probability: number;
  threshold: number;
  vessels?: VesselMetrics;
}

export interface HeartFactor {
  feature: string;
  label: string;
  value: number;
  display?: string;
  impact: number;
}

export interface ImageSet {
  steps: Record<string, string | null>;
  wavelet: Record<string, string | null>;
  heatmap: string | null;
  vessels: string | null;
}

export interface ScreeningFull extends ScreeningSummary {
  patient: { id: number; code: string; name: string; age: number; sex: string };
  image_name: string;
  quality: QualityReport;
  retina: RetinaFindings;
  clinical: Record<string, number> | null;
  heart: { probability: number; factors: HeartFactor[] } | null;
  stage_detail: StageDetail | null;
  images: ImageSet;
}

export interface Sample {
  name: string;
  label: 0 | 1;
  url: string;
}

export interface ConfusionMatrix {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
}

export interface RocCurve {
  fpr: number[];
  tpr: number[];
}

export interface ModelTest {
  n: number;
  threshold: number;
  accuracy: number;
  sensitivity: number;
  specificity: number;
  precision?: number;
  f1: number;
  roc_auc: number;
  confusion_matrix: ConfusionMatrix;
  roc_curve: RocCurve;
}

export interface ModelMetrics {
  model: string;
  dataset: string;
  split: Record<string, number>;
  epochs?: number;
  cv_roc_auc_mean?: number;
  notes?: string;
  test: ModelTest;
}

export interface MetricsResponse {
  generated_at?: string;
  retina?: ModelMetrics;
  heart?: ModelMetrics;
}

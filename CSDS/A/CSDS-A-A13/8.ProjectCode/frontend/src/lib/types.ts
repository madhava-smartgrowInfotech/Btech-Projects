export type Role = "admin" | "invigilator";
export type UserStatus = "active" | "pending" | "disabled";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  status: UserStatus;
  created_at: string;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
}

export interface Rules {
  adjacency: 4 | 8;
  roll_gap: number;
  department_mix: boolean;
  fill_strategy: "compact" | "balanced";
  accessible_per_hall: number;
}

export interface DemoInfo {
  enabled: boolean;
  password: string | null;
  accounts: { role: Role; email: string; name: string }[];
}

// ---------------------------------------------------------------- import
export type ImportKind = "courses" | "candidates" | "halls" | "timetable" | "workbook";
export type DataKind = Exclude<ImportKind, "workbook">;

export interface ImportIssue {
  kind: DataKind;
  row: number | null;
  column: string | null;
  message: string;
  level: "error" | "warning";
}

export interface ImportKindReport {
  rows_total: number;
  rows_valid: number;
  new: number;
  updated: number;
  errors: number;
  warnings: number;
}

export interface ImportReport {
  mode: "update" | "replace";
  kinds: Partial<Record<DataKind, ImportKindReport>>;
  errors: number;
  warnings: number;
  issues: ImportIssue[];
  issues_truncated: boolean;
  preview: Partial<Record<DataKind, Record<string, string | null>[]>>;
}

export interface ImportBatch {
  id: number;
  kind: ImportKind;
  filename: string;
  status: "validated" | "failed" | "committed";
  rows_total: number;
  rows_valid: number;
  created_at: string;
  committed_at: string | null;
  created_by: string | null;
  report: ImportReport | null;
}

// ---------------------------------------------------------------- data
export interface DataSummary {
  departments: number;
  courses: number;
  candidates: number;
  accessible_candidates: number;
  registrations: number;
  halls: number;
  active_halls: number;
  seats: number;
  sessions: number;
  papers: number;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  courses: number;
  candidates: number;
}

export interface Course {
  id: number;
  code: string;
  name: string;
  department_code: string;
  department_name: string;
  candidates: number;
  session_id: number | null;
  session_label: string | null;
  paper_group: string | null;
}

export interface Candidate {
  id: number;
  roll_no: string;
  full_name: string;
  department_code: string;
  department_name: string;
  email: string | null;
  date_of_birth: string | null;
  needs_accessible_seat: boolean;
  courses: string[];
}

export interface CandidatePage {
  items: Candidate[];
  total: number;
  page: number;
  page_size: number;
}

export interface CandidateSeat {
  plan_id: number;
  plan_status: string;
  session_id: number;
  session_label: string;
  date: string;
  start_time: string;
  end_time: string;
  course_code: string;
  course_name: string;
  hall_code: string;
  hall_name: string;
  seat_label: string;
}

export interface CandidateDetail extends Candidate {
  seats: CandidateSeat[];
}

export interface Hall {
  id: number;
  code: string;
  name: string;
  building: string;
  floor: string;
  rows: number;
  cols: number;
  capacity: number;
  blocked_seats: string[];
  accessible_seats: string[];
  aisles_after_cols: number[];
  is_active: boolean;
  paper_ceiling: number;
}

export interface SessionPaper {
  course_id: number;
  course_code: string;
  course_name: string;
  department_code: string;
  paper_group: string | null;
  candidates: number;
}

export interface ExamSession {
  id: number;
  code: string;
  label: string;
  date: string;
  start_time: string;
  end_time: string;
  papers: SessionPaper[];
  candidates: number;
  accessible_candidates: number;
  plans: { count: number; latest_id: number | null; latest_status: PlanStatus | null; published_id: number | null };
}

// ---------------------------------------------------------------- plans
export type PlanStatus = "draft" | "published" | "archived";

export interface Violation {
  type: "same_paper" | "roll_gap" | "accessible" | "capacity";
  hall: string;
  seats: string[];
  candidates: string[];
  detail: string;
}

export interface HallCard {
  hall: string;
  seats: number;
  placed: number;
  utilisation: number;
  papers: Record<string, number>;
  departments: Record<string, number>;
  same_paper_pairs: number;
  roll_gap_violations: number;
  same_department_pairs: number;
  neighbour_pairs: number;
}

export interface Scorecard {
  candidates: number;
  placed: number;
  unplaced: number;
  capacity_violations: number;
  same_paper_pairs: number;
  roll_gap_violations: number;
  accessible_violations: number;
  same_department_pairs: number;
  neighbour_pairs: number;
  halls_used: number;
  seats_in_used_halls: number;
  utilisation: number;
  hard_ok: boolean;
  per_hall: HallCard[];
  violations: Violation[];
}

export interface SessionRef {
  id: number;
  code: string;
  label: string;
  date: string;
  start_time: string;
  end_time: string;
}

export interface PersonRef {
  id: number;
  full_name: string;
}

export interface PlanSummary {
  id: number;
  session: SessionRef;
  version: number;
  status: PlanStatus;
  seed: number;
  solve_ms: number;
  swaps: number;
  created_at: string;
  created_by: string | null;
  published_at: string | null;
  candidates: number;
  halls_used: number;
  utilisation: number;
  same_paper_pairs: number;
  roll_gap_violations: number;
  accessible_violations: number;
  same_department_pairs: number;
  hard_ok: boolean;
  conflicts_avoided: number | null;
}

export interface PlanHall {
  hall_id: number;
  code: string;
  name: string;
  building: string;
  capacity: number;
  placed: number;
  utilisation: number;
  papers: Record<string, number>;
  same_department_pairs: number;
  invigilators: PersonRef[];
}

export interface PlanDetail extends PlanSummary {
  rules: Rules;
  hall_ids: number[];
  engine_version: string;
  data_fingerprint: string;
  solver_hash: string;
  assignment_hash: string;
  scorecard: Scorecard;
  baseline: Baseline;
  stats: { hall_budget?: number; attempts?: number; stage_a_ms?: number; stage_b_ms?: number; halls_used?: number; retries?: number };
  halls: PlanHall[];
}

export interface VerifyResult {
  plan_id: number;
  seed: number;
  data_unchanged: boolean;
  reproduced: boolean;
  stored_solver_hash: string;
  recomputed_hash: string | null;
  manual_moves: number;
  engine_version: string;
  solve_ms: number | null;
}

export interface AuditEvent {
  id: number;
  at: string;
  action: string;
  summary: string;
  actor: string | null;
  plan_id: number | null;
  details: Record<string, unknown>;
}

export interface Baseline {
  method?: string;
  same_paper_pairs?: number;
  roll_gap_violations?: number;
  same_department_pairs?: number;
  accessible_violations?: number;
  neighbour_pairs?: number;
}

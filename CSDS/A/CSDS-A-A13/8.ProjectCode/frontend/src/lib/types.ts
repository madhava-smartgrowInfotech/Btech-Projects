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

export interface MapSeat {
  label: string;
  row: number;
  col: number;
  candidate: { id: number; roll_no: string; full_name: string; department: string };
  course_code: string;
  course_name: string;
  paper: string;
  colour: number;
  needs_accessible: boolean;
  attendance: "present" | "absent" | null;
}

export interface HallMap {
  plan: {
    id: number;
    version: number;
    status: PlanStatus;
    seed: number;
    adjacency: number;
    roll_gap: number;
    session: { id: number; label: string; date: string; start_time: string; end_time: string };
  };
  hall: {
    id: number;
    code: string;
    name: string;
    building: string;
    floor: string;
    rows: number;
    cols: number;
    blocked: string[];
    accessible: string[];
    aisles: number[];
    capacity: number;
  };
  legend: { paper: string; courses: string[]; count: number; colour: number }[];
  seats: MapSeat[];
  violations: Violation[];
  stats: Partial<HallCard>;
  invigilators: PersonRef[];
  attendance: { present: number; absent: number; submitted_at: string | null; can_mark: boolean };
  can_edit: boolean;
  halls: { hall_id: number; code: string; name: string; placed: number }[];
}

export interface AttendanceCounts {
  total: number;
  present: number;
  absent: number;
  unmarked: number;
  submitted_at: string | null;
}

export interface AttendanceAssignment extends AttendanceCounts {
  plan_id: number;
  plan_version: number;
  session: { id: number; label: string; date: string; start_time: string; end_time: string };
  hall: { id: number; code: string; name: string; building: string; floor: string };
  invigilators: string[];
  mine: boolean;
}

export interface ScanResult {
  candidate: { id: number; roll_no: string; full_name: string };
  seat: string;
  already_present: boolean;
  counts: AttendanceCounts;
}

// ---------------------------------------------------------------- analytics
export interface PlanBrief {
  id: number;
  version: number;
  status: PlanStatus;
  solve_ms: number;
  halls_used: number;
  utilisation: number;
  candidates: number;
  same_paper_pairs: number;
  same_department_pairs: number;
  hard_ok: boolean;
  conflicts_avoided: number;
  swaps: number;
}

export interface Overview {
  counts: { candidates: number; halls: number; sessions: number; plans: number; published: number; seated: number };
  totals: {
    conflicts_avoided: number;
    same_paper_pairs: number;
    avg_solve_ms: number | null;
    max_solve_ms: number | null;
    hard_ok_rate: number | null;
    manual_moves: number;
  };
  attendance: { total: number; present: number; absent: number; unmarked: number; rate: number | null };
  sessions: {
    id: number;
    label: string;
    date: string;
    start_time: string;
    candidates: number;
    papers: number;
    plans: number;
    published_plan: PlanBrief | null;
    attendance: { total: number; present: number; absent: number; unmarked: number } | null;
  }[];
  solve_times: { plan_id: number; label: string; session_id: number; version: number; candidates: number; solve_ms: number; created_at: string; status: PlanStatus }[];
  hall_usage: { hall: string; name: string; sittings: number; utilisation: number }[];
}

export interface PlanAnalytics {
  plan: PlanBrief;
  session: { id: number; label: string };
  halls: { hall: string; seats: number; placed: number; utilisation: number; papers: number; departments: Record<string, number>; same_department_pairs: number; neighbour_pairs: number }[];
  department_codes: string[];
  comparison: { measure: string; seatwise: number; baseline: number | null }[];
  neighbour_pairs: { total: number; same_paper: number; same_department: number; mixed: number };
  attendance: { hall: string; total: number; present: number; absent: number }[];
}

export interface BenchmarkSummaryRow {
  scenario: string;
  method: string;
  runs: number;
  solved_rate: number;
  solve_s_mean: number;
  solve_s_min: number;
  solve_s_max: number;
  same_paper_pairs_mean?: number | null;
  roll_gap_violations_mean?: number | null;
  accessible_violations_mean?: number | null;
  same_department_pairs_mean?: number | null;
  neighbour_pairs_mean?: number | null;
  utilisation_mean?: number | null;
  halls_used_mean?: number | null;
  hard_rules_satisfied_rate: number;
}

export interface EngineInfo {
  profile: { engine_version: string; hall_budget: number; hall_budget_in_use: number; experiment: string | null; tuned_at?: string; ortools_version?: string; source: string };
  available: boolean;
  metrics: null | {
    run: string;
    run_date: string;
    engine_version: string;
    ortools_version: string;
    machine: { platform: string; processor: string; cpu_threads: number; python: string };
    dataset: { type: string; split: string; scenarios: { name: string; candidates: number; papers: number; departments: number; adjacency: number; roll_gap: number; halls: number; seats: number }[]; seeds: number[] };
    per_hall_budget: number | null;
    headline: {
      scenario: string;
      candidates: number;
      solve_s_mean: number;
      hard_rules_satisfied_rate: number;
      same_paper_pairs: number;
      conflicts_avoided_vs_sequential: number;
      abs_roll_seat_correlation: number;
      neighbour_overlap: number;
      all_scenarios_solved: boolean;
      all_hard_rules_satisfied: boolean;
      max_solve_s: number;
    };
    summary: BenchmarkSummaryRow[];
    predictability: Record<string, { seeds: number; abs_roll_seat_correlation: number; neighbour_overlap: number | null; front_row_bias_pp: number }>;
    tuning: null | { budgets: { budget: number; all_hard_rules_satisfied: boolean; same_department_pairs_mean: number; session_solve_s_mean: number }[]; chosen_budget: number; tolerance: number };
    plots: string[];
  };
  plots: string[];
}

export interface SwapTarget {
  seat: string;
  occupied: boolean;
  ok: boolean;
  reasons: string[];
  notes: string[];
}

export interface SwapOptions {
  seat: string;
  candidate: string;
  targets: SwapTarget[];
}

export interface Baseline {
  method?: string;
  same_paper_pairs?: number;
  roll_gap_violations?: number;
  same_department_pairs?: number;
  accessible_violations?: number;
  neighbour_pairs?: number;
}

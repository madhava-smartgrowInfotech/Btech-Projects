/** Shapes returned by the AutoSecAI API (see backend/main.py and autosecai/agents.py). */

export interface User {
  id: number;
  email: string;
  name: string;
  created: string;
  is_demo: boolean;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Verdict = "BLOCK" | "REQUEST_CHANGES" | "APPROVE";

export interface Finding {
  id: string;
  rule_id: string;
  title: string;
  category: "security" | "quality";
  severity: Severity;
  confidence: "high" | "medium" | "low";
  cwe: string;
  owasp: string;
  file: string;
  line: number;
  end_line: number;
  function: string;
  snippet: string;
  detector: string;
  in_diff: boolean;
  explanation: string;
  static_explanation: string;
  llm: boolean;
  impact: string;
  exploit: string;
  remediation: string;
  safe_example: string;
  flow: string[];
  corroboration: string;
  ml: number | null;
  patch: string;
  fix_note: string;
  fix_verified: boolean;
  evidence: string;
}

export interface MlRow {
  file: string;
  function: string;
  line: number;
  probability: number;
  vuln_type: string | null;
  drivers: { feature: string; contribution: number; value: number; safe_mean: number }[];
  metrics: Record<string, number>;
}

export interface TraceItem {
  agent: string;
  role: string;
  seconds: number;
  summary: string;
  details: string[];
}

export interface FuncRow {
  name: string;
  file: string;
  line: number;
  cyclomatic: number;
  max_nesting: number;
  n_params: number;
  loc: number;
  in_diff?: boolean;
}

export interface Review {
  id: string;
  created: string;
  title: string;
  source: string;
  score: number;
  verdict: Verdict;
  summary: string;
  findings: Finding[];
  ml: MlRow[];
  functions: FuncRow[];
  trace: TraceItem[];
  files: { path: string; status: string; added: number; removed: number; language: string }[];
  patched: Record<string, string>;
  stats: {
    by_severity: Record<Severity, number>;
    by_category: Record<string, number>;
    by_cwe: Record<string, number>;
    by_file: Record<string, number>;
    preexisting: number;
    files: number;
    lines_added: number;
    lines_removed: number;
    functions_scored: number;
    functions_flagged: number;
    autofix: number;
    autofix_verified: number;
  };
}

export interface ReviewRow {
  id: string;
  created: string;
  title: string;
  source: string;
  score: number;
  verdict: Verdict;
  findings: number;
  security: number;
}

export interface Job<T = Record<string, unknown>> {
  id: string;
  kind: string;
  status: "running" | "done" | "error";
  messages: string[];
  result: T | null;
  error: string | null;
  seconds: number | null;
}

export interface MetricInfo {
  id: string;
  key: string;
  name: string;
  meaning: string;
  label: string;
  safe_mean: number;
}

export interface Meta {
  version: string;
  severities: Severity[];
  pipeline: { name: string; text: string }[];
  suggested: string[];
  llm_env: boolean;
  metrics: MetricInfo[];
}

export interface Samples {
  demo_diff: string;
  before: string;
  after: string;
  filename: string;
  repo_files: string[];
}

export interface PublicStats {
  functions: number;
  vulnerable: number;
  best_model: string;
  f1: number;
  accuracy: number;
  recall: number;
  type_accuracy: number;
  metrics: number;
  models: number;
  selectors: number;
  agents: number;
}

export interface PublicExample {
  verdict: Verdict;
  score: number;
  files: number;
  security: number;
  finding: Pick<Finding, "title" | "file" | "line" | "severity" | "cwe" | "snippet" | "explanation" | "remediation" | "patch" | "fix_verified">;
}

export interface Hit {
  file: string;
  name: string;
  kind: string;
  line: number;
  end: number;
  score: number;
  doc: string;
  why: string[];
  code: string;
  decorators: string[];
  callers: string[];
  callees: string[];
}

export interface AskResult {
  answer: string;
  hits: Hit[];
  intents: string[];
}

export interface RepoIndexInfo {
  index_id: string;
  name: string;
  files: number;
  units: number;
  guide: string;
  overview: {
    files: number;
    loc: number;
    functions: number;
    classes: number;
    import_edges: number;
    languages: Record<string, number>;
    entry_points: string[];
    routes: { method: string; path: string; handler: string; file: string; line: number }[];
    hotspots: { name: string; file: string; line: number; cyclomatic: number }[];
    by_concept: { key: string; label: string; files: string[] }[];
  };
  graph: { nodes: { id: string; label: string; x: number; y: number; degree: number }[]; edges: [string, string][] };
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  auc: number;
}

export interface LabReport {
  n_functions: number;
  n_vulnerable: number;
  class_ratio: number;
  train_size: number;
  test_size: number;
  balanced_train_size: number;
  tomek_removed: number;
  best_k: number;
  k_scores: Record<string, number>;
  selected_labels: string[];
  fs_scores: Record<string, Record<string, number>>;
  fs_order: { votes: Record<string, number>; mean_rank: Record<string, number> };
  results: Record<string, ModelMetrics>;
  best: string;
  roc: Record<string, { fpr: number[]; tpr: number[] }>;
  confusion: Record<string, number[][]>;
  ablation: Record<string, { recall: number; precision: number; f1: number }>;
  importance: Record<string, number>;
  type_accuracy: number;
  type_report: Record<string, { precision: number; recall: number; "f1-score": number; support: number }>;
  type_importance: Record<string, number>;
  type_counts: Record<string, number>;
  seconds: number;
}

export interface LabAnalysis {
  functions: {
    name: string;
    probability: number;
    vuln_type: string | null;
    drivers: { feature: string; value: number; safe_mean: number }[];
    metrics: { key: string; label: string; value: number }[];
  }[];
  findings: { rule_id: string; line: number; severity: Severity; title: string }[];
}

export type ReviewOptions = {
  ml: boolean;
  min_severity: Severity;
  use_llm: boolean;
  api_key: string | null;
  gh_token: string | null;
};

export type Language = "en" | "hi" | "te";

export interface User {
  id: number;
  email: string;
  full_name: string;
  language: Language;
  theme: "light" | "dark" | "system";
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  expires_at: string;
  user: User;
}

export type DocStatus = "queued" | "parsing" | "indexing" | "extracting" | "ready" | "failed";

export interface DocumentInfo {
  id: number;
  file_name: string;
  size_bytes: number;
  page_count: number;
  insurer: string | null;
  product_name: string | null;
  uin: string | null;
  status: DocStatus;
  status_detail: string | null;
  progress: number;
  error: string | null;
  extraction_error: string | null;
  is_sample: boolean;
  processed_at: string | null;
}

export interface Policy {
  id: number;
  display_name: string;
  is_sample: boolean;
  created_at: string;
  document: DocumentInfo;
  has_card: boolean;
  clause_count: number;
  risk_counts: Partial<Record<Severity, number>>;
  highlights: Record<string, string>;
}

export interface PolicyStatus {
  id: number;
  status: DocStatus;
  status_detail: string | null;
  progress: number;
  error: string | null;
  extraction_error: string | null;
  has_card: boolean;
}

export interface Sourced {
  value: string;
  number: number | null;
  unit: string;
  found: boolean;
  quote: string | null;
  clause_ordinal: number | null;
  clause_ref: string | null;
  clause_label: string | null;
  page: number | null;
  verified: boolean;
  name?: string;
}

export interface CardData {
  insurer: string;
  product_name: string;
  uin: string | null;
  policy_type: string;
  specific_disease_examples: string[];
  waiting_periods: Record<string, Sourced>;
  claim_timelines: Record<string, Sourced>;
  co_payment_conditions: Sourced[];
  sub_limits: Sourced[];
  key_exclusions: Sourced[];
  [key: string]: unknown;
}

export interface CardSummary {
  overview: string;
  best_for: string[];
  watch_outs: string[];
  next_actions: string[];
}

export interface PolicyCardResponse {
  policy_id: number;
  document_id: number;
  language: Language;
  model: string;
  prompt_version: string;
  created_at: string;
  verified_ratio: number;
  translated: boolean;
  data: CardData;
  summary: CardSummary | null;
  labels: {
    fields: Record<string, string>;
    waiting_periods: Record<string, string>;
    claim_timelines: Record<string, string>;
  };
}

export type Severity = "high" | "medium" | "low";

export interface Risk {
  id: number;
  title: string;
  category: string;
  severity: Severity;
  explanation: string;
  clause_ordinal: number | null;
  clause_label: string | null;
  page: number | null;
  quote: string | null;
  source: "rule" | "ai";
}

export interface BBox {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface Clause {
  id: number;
  ordinal: number;
  clause_ref: string | null;
  heading: string | null;
  section_path: string | null;
  text: string;
  page_start: number;
  page_end: number;
  bboxes: BBox[];
  label: string;
}

export interface PageInfo {
  number: number;
  width: number;
  height: number;
}

export interface Citation {
  ordinal: number;
  tag: string;
  clause_ref: string | null;
  heading: string | null;
  label: string;
  page: number;
  page_end: number;
  quote: string;
  bboxes: BBox[];
}

export interface FaithfulnessClaim {
  text: string;
  clauses: number[];
  support: number;
  contradiction: number;
  evidence: string | null;
  numbers_ok: boolean;
  note: string | null;
}

export interface Faithfulness {
  score: number | null;
  label: "well_supported" | "partly_supported" | "weakly_supported" | "not_applicable";
  claims: FaithfulnessClaim[];
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  content_en: string | null;
  language: Language;
  status: "answered" | "partial" | "not_in_policy" | null;
  citations: Citation[] | null;
  faithfulness: number | null;
  faithfulness_detail: Faithfulness | null;
  retrieval: {
    query?: string;
    items?: { ordinal: number; label: string; page: number; bm25_rank: number | null; dense_rank: number | null; rerank: number | null }[];
    follow_ups?: string[];
  } | null;
  timings: Record<string, number | Record<string, number>> | null;
  total_ms: number | null;
  model: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  policy_id: number;
  policy_name: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Exchange {
  question: Message;
  answer: Message;
  follow_ups: string[];
}

export type Verdict = "covered" | "partly_covered" | "not_covered" | "needs_info";
export type CheckStatus = "pass" | "fail" | "unknown" | "warning";

export interface ClauseRef {
  ordinal: number | null;
  label?: string;
  page: number | null;
}

export interface ClaimResult {
  verdict: Verdict;
  model_verdict: Verdict;
  verdict_summary: string;
  verdict_summary_en: string;
  reasons: { text: string; text_en: string; clauses: ClauseRef[] }[];
  prechecks: { check: string; status: CheckStatus; detail: string; source: "rule" | "ai"; clauses?: ClauseRef[]; clause_ordinal?: number | null; page?: number | null }[];
  documents: { id: string; item: string; why: string; clauses: ClauseRef[] }[];
  steps: { title: string; detail: string; timeline: string | null; clauses: ClauseRef[] }[];
  cost_notes: string[];
  estimate: {
    estimated_cost: number;
    deductible: number;
    co_payment_percent: number;
    co_payment_amount: number;
    insurer_pays: number;
    you_pay: number;
    notes: string[];
  } | null;
  matched_specific_disease: string | null;
  citations: Citation[];
  faithfulness: Faithfulness;
  timings: Record<string, number | Record<string, number>>;
  model: string;
}

export interface ClaimCase {
  id: number;
  policy_id: number;
  policy_name: string;
  treatment: string;
  inputs: Record<string, unknown>;
  result: ClaimResult;
  verdict: Verdict;
  checklist_state: Record<string, boolean>;
  language: Language;
  faithfulness: number | null;
  total_ms: number | null;
  model: string | null;
  created_at: string;
}

export interface CompareCell {
  value: string | null;
  found: boolean | null;
  clause_ordinal: number | null;
  page: number | null;
  verified: boolean | null;
}

export interface ComparisonResult {
  rows: { key: string; label: string; better: "a" | "b" | "equal" | null; a: CompareCell; b: CompareCell }[];
  risk_counts: { a: Partial<Record<Severity, number>>; b: Partial<Record<Severity, number>> };
  overall: string;
  choose_a_if: string[];
  choose_b_if: string[];
  trade_offs: { topic: string; policy_a: string; policy_b: string; better: string; why: string; tags: { policy: "a" | "b"; ordinal: number }[] }[];
  next_actions: string[];
  model: string;
  timings: { total_ms: number };
}

export interface Comparison {
  id: number;
  policy_a_id: number;
  policy_b_id: number;
  policy_a_name: string;
  policy_b_name: string;
  language: Language;
  result: ComparisonResult;
  model: string | null;
  total_ms: number | null;
  created_at: string;
}

export interface DashboardSummary {
  kpis: {
    policies: number;
    ready_policies: number;
    questions: number;
    avg_faithfulness: number | null;
    median_response_ms: number | null;
    claim_checks: number;
    comparisons: number;
    high_risks: number;
    ai_calls: number;
    ai_tokens: number;
  };
  activity_by_day: { date: string; questions: number; claim_checks: number }[];
  faithfulness_bins: { bin: string; count: number }[];
  verdicts: { verdict: Verdict; count: number }[];
  risks_by_policy: { policy: string; high: number; medium: number; low: number }[];
  response_times: { n: number; ms: number; faithfulness: number | null }[];
  recent: { type: "policy" | "claim" | "chat"; title: string; at: string; link: string; verdict?: Verdict }[];
}

export interface SearchItem {
  score: number;
  bm25: number | null;
  bm25_rank: number | null;
  dense: number | null;
  dense_rank: number | null;
  rrf: number | null;
  rerank: number | null;
  clause: {
    id: number;
    ordinal: number;
    clause_ref: string | null;
    heading: string | null;
    section_path: string | null;
    page_start: number;
    page_end: number;
    text: string;
    label: string;
    bboxes: BBox[];
  };
}

export interface SearchResponse {
  query: string;
  mode: string;
  timings_ms: Record<string, number>;
  items: SearchItem[];
}

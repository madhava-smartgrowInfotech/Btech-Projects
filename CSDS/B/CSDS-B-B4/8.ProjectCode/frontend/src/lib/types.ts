export type Level = "low" | "medium" | "high";
export type Lang3 = { en: string; hi: string; te: string };

export interface Party {
  upi_id: string;
  name: string;
  is_merchant: boolean;
  category: string | null;
  is_sample: boolean;
}

export interface TrustComponent {
  code: string;
  delta: number;
}

export interface Trust {
  score: number;
  band: "trusted" | "caution" | "risky";
  components: TrustComponent[];
  account_age_days: number;
  report_count: number;
  report_score: number;
  distinct_payers_24h: number;
  distinct_payers_7d: number;
  new_payer_share_7d: number;
  distinct_payers_90d: number;
  collect_targets_7d: number;
  is_merchant: boolean;
}

export interface Reason {
  code: string;
  params: Record<string, string | number>;
  feature: string;
  contribution: number;
  kind: "model" | "guard" | "reassurance";
  text: Lang3;
}

export interface Highlight {
  start: number;
  end: number;
  text: string;
  sources: string[];
  rules: string[];
}

export interface NoteAnalysis {
  score: number;
  verdict: "safe" | "suspicious" | "scam";
  promises_money: boolean;
  highlights: Highlight[];
  scam_type: string | null;
}

export interface Guard {
  type?: "collect" | "qr";
  is_debit?: boolean;
  debit_amount?: number;
  note?: NoteAnalysis;
  flags?: string[];
  note_score?: number;
  qr_flag?: number;
  payee_name_in_qr?: string | null;
  registered_name?: string | null;
  linked_sms_id?: number | null;
  requester_trust?: Trust;
}

export interface Assessment {
  score: number;
  level: Level;
  final_level: Level;
  action: "pay" | "verify" | "hold" | "block";
  probability: number;
  behaviour_score: number;
  behaviour_top_feature: string | null;
  payee_trust: number;
  trust: Trust | null;
  reasons: Reason[];
  reassurance: Reason[];
  contributions: { feature: string; value: number }[];
  base_value: number;
  features: Record<string, number>;
  guard: Guard;
  local_time: string | null;
  sandbox_clock: boolean;
  model_version: string;
  created_at: string;
}

export interface Warning {
  scam_type: string;
  name: Lang3;
  advice: Lang3;
}

export interface IntentInfo {
  purpose: string;
  answers: Record<string, unknown>;
  matched_scam_type: string | null;
  escalated: boolean;
  warning: Warning | null;
}

export interface HoldInfo {
  id: number;
  status: "active" | "released" | "cancelled" | "rejected" | "expired";
  hold_minutes: number;
  hold_until: string;
  needs_approval: boolean;
  approval_status: "none" | "pending" | "approved" | "rejected";
  approver_user_id: number | null;
  decided_at: string | null;
}

export interface Question {
  id: string;
  type: "choice" | "yes_no";
  options?: string[];
  only_for_purpose?: string[];
}

export type PaymentStatus = "draft" | "completed" | "held" | "cancelled" | "rejected" | "failed" | "declined" | "blocked";

export interface Payment {
  id: number;
  reference: string;
  direction: "sent" | "received";
  counterparty: Party;
  amount: number;
  note: string | null;
  channel: "send" | "qr" | "collect";
  status: PaymentStatus;
  status_reason: string | null;
  created_at: string;
  completed_at: string | null;
  level: Level | null;
  score: number | null;
  assessment?: Assessment | null;
  intent?: IntentInfo | null;
  hold?: HoldInfo | null;
  questions?: Question[];
}

export interface IntentResult {
  purpose: string;
  signals: string[];
  scam_type: string | null;
  escalated: boolean;
  final_level: Level;
  recommend_cancel: boolean;
  warning: Warning | null;
}

export interface CollectItem {
  id: number;
  direction: "incoming" | "outgoing";
  counterparty: Party;
  amount: number;
  note: string | null;
  status: string;
  guard: (Guard & { requester_trust?: Trust }) | null;
  expires_at: string;
  created_at: string;
}

export interface SmsResult {
  id: number;
  text: string;
  language: "en" | "hi" | "te";
  script: string | null;
  verdict: "safe" | "suspicious" | "scam";
  probability: number;
  model_probability: number | null;
  rules_score: number | null;
  scam_type: string | null;
  scam_type_name: Lang3 | null;
  advice: Lang3 | null;
  highlights: Highlight[];
  signals: { rule: string; weight: number; category: string | null }[];
  model_terms: { term: string; weight: number }[];
  entities: { upi_ids: string[]; urls: string[]; phones: string[]; amounts: number[] };
  linked_accounts: { upi_id: string; in_sandbox: boolean; name: string | null }[];
  thresholds: { scam: number; suspicious: number };
  created_at: string;
}

export interface QrResult {
  valid: boolean;
  raw: string;
  payee_upi_id?: string;
  payee_name_in_qr?: string | null;
  registered_name?: string | null;
  amount?: number | null;
  note?: string | null;
  note_analysis?: NoteAnalysis;
  flags: string[];
  qr_flag: number;
  is_self?: boolean;
}

export interface WalletInfo {
  upi_id: string;
  display_name: string;
  balance: number;
  is_sample: boolean;
  qr_uri: string;
  stats: {
    spent_this_month: number;
    received_this_month: number;
    payments_checked: number;
    payments_stopped: number;
    money_protected: number;
    on_hold: number;
    levels_30d: Record<Level, number>;
  };
  daily_spend: { date: string; amount: number }[];
}

export interface PayeeLookup extends Party {
  is_self: boolean;
  times_paid: number;
  saved_as: string | null;
  trust: Trust;
}

export interface SavedPayee extends Party {
  nickname?: string;
  relation?: string | null;
  times_paid: number;
}

export interface Settings {
  language: "en" | "hi" | "te";
  voice_enabled: boolean;
  auto_speak: boolean;
  hold_minutes: number;
  hold_choices: number[];
  trusted_approval_required: boolean;
  has_trusted_approver: boolean;
  sandbox_clock: string | null;
}

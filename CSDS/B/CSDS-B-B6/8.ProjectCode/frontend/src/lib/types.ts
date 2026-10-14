/** Shapes returned by the UniHealth platform API (see docs/FRONTEND_PLAN.md). */

export interface Source {
  hospital: string;
  name: string;
  local_id: string;
  confidence: number;
  status: string;
  counts: Record<string, number>;
}

export interface TimelineItem {
  id: string;
  type: string;
  category: string;
  hospital: string;
  hospital_name: string;
  date: string | null;
  title: string;
  value: string;
  status: string;
}

export interface RecordView {
  person: { id: string; name: string; birth_date: string; gender: string };
  categories: string[];
  sources: Source[];
  timeline: TimelineItem[];
  counts: Record<string, number>;
}

export interface Factor {
  feature: string;
  label: string;
  value: number | string;
  date: string | null;
  impact: number;
  direction: string;
}

export interface RiskScore {
  model: string;
  probability: number;
  level: "high" | "moderate" | "low";
  top_factors: Factor[];
  inputs: { label: string; from_record: boolean }[];
}

export interface RiskPanelData {
  person: RecordView["person"];
  heart: RiskScore;
  diabetes: RiskScore;
  disclaimer: string;
}

export interface AssistantReply {
  title?: string;
  values?: string[];
  language: string;
  text: string;
  disclaimer: string;
}

export interface Consent {
  id: string;
  hospital: string;
  hospital_name: string;
  categories: string[];
  status: "active" | "inactive";
  expires: string | null;
  created_at: string;
  updated_at: string;
  fhir: Record<string, unknown>;
}

export interface AccessRequest {
  id: number;
  person_id: string;
  doctor: string;
  hospital: string;
  hospital_name: string;
  reason: string;
  status: "blocked" | "granted" | "approved";
  created_at: string;
}

export interface Reminder {
  id: number;
  kind: string;
  text: string;
  due: string;
  done: boolean;
  state: "done" | "overdue" | "due today" | "upcoming";
  source: string;
}

export interface HospitalStatus {
  key: string;
  name: string;
  base_url: string;
  online: boolean;
  counts: Record<string, number>;
  fhir_version?: string;
  error?: string;
}

export interface HospitalPatient {
  hospital: string;
  local_id: string;
  given: string[];
  family: string;
  name: string;
  birth_date: string;
  gender: string;
  phone: string;
}

export interface PushedSummary {
  id: number;
  person_id: string | null;
  hospital: string;
  hospital_name: string;
  local_id: string;
  entries: number;
  received_at: string;
}

export interface VisitResult {
  created: { entry: unknown[] };
  sync: { pushed_entries: number; platform: { person_id: string | null; reminders_added: number } };
}

export interface MpiSearchResult {
  person_id: string;
  name: string;
  birth_date: string;
  gender: string;
  match: number;
  hospitals: { key: string; name: string; local_id: string; confidence: number }[];
}

export interface MpiPerson {
  person_id: string;
  name: string;
  birth_date: string;
  gender: string;
  links: { hospital: string; local_id: string; name: string; birth_date: string; phone: string; confidence: number }[];
}

export interface Verification {
  intact: boolean;
  entries: number;
  head?: string;
  broken_at?: number;
  position?: number;
}

export interface AuditEntry {
  id: number;
  ts: string;
  actor: string;
  action: string;
  person_id: string | null;
  detail: Record<string, unknown>;
  hash: string;
  prev_hash: string;
}

export interface AuditLog {
  entries: AuditEntry[];
  verification: Verification;
}

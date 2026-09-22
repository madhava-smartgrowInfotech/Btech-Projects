import type { ZoneLabel } from "./zones";

export type ComplaintStatus = "detected" | "registered" | "acknowledged" | "in_progress" | "resolved" | "verified" | "dismissed";

export interface ComplaintEvent {
  id: number;
  ts: string;
  kind: string;
  from_status: string | null;
  to_status: string | null;
  actor_label: string;
  note: string | null;
}

export interface Complaint {
  id: number;
  ref_code: string;
  h3_cell: string;
  operator: string;
  lat: number;
  lon: number;
  status: ComplaintStatus;
  severity: "weak" | "dead";
  origin: "auto" | "user";
  source: string;
  reporter_user_id: number | null;
  assigned_to_id: number | null;
  assigned_to_name: string | null;
  reporter_name: string | null;
  summary: string | null;
  reopen_count: number;
  detected_at: string;
  registered_at: string | null;
  acknowledged_at: string | null;
  in_progress_at: string | null;
  resolved_at: string | null;
  verified_at: string | null;
  dismissed_at: string | null;
  updated_at: string;
  readings: number;
  bad_share: number | null;
  verification: { state: string; readings?: number; strong_share?: number; bad_share?: number; needed?: number } | null;
}

export interface Evidence {
  zone: { h3_cell: string; center: [number, number]; area_km2?: number; operator: string };
  window: { first: string | null; last: string | null; minutes: number };
  readings: number;
  classes: Record<ZoneLabel, number>;
  bad_share: number;
  dead_share?: number;
  devices: number;
  sources: Record<string, number>;
  methods?: Record<string, number>;
  model_versions?: string[];
  mean_confidence?: number | null;
  service?: { readings: number; no_connectivity_share: number; latency_median_ms: number | null; latency_p90_ms: number | null; jitter_median_ms: number | null; packet_loss_mean: number | null; download_median_mbps: number | null; upload_median_mbps: number | null; asns: number[]; radio_estimate: Record<string, number> };
  radio?: { readings: number; rsrp_median_dbm: number | null; rsrp_min_dbm: number | null; rsrq_median_db: number | null; sinr_median_db: number | null; rssi_median_dbm: number | null; cell_ids: number[]; pcis: number[]; earfcns: number[]; network_types: Record<string, number> };
  wifi?: { readings: number; rssi_median_dbm: number | null; latency_median_ms: number | null; offline_share: number };
  top_reasons?: { reason: string; count: number }[];
  series?: { ts: string; label: ZoneLabel; rsrp: number | null; latency_ms: number | null; dl_mbps: number | null; wifi_rssi: number | null }[];
  samples?: Record<string, unknown>[];
  nearest_strong_spot?: { found: boolean; status: string; message: string; lat: number | null; lon: number | null; distance_m: number | null; direction: string | null; predicted: number | null; predicted_mbps?: number; probability: number | null; target: string } | null;
  latest?: { readings: number; bad_share: number; last: string; classes: Record<string, number> };
}

export interface ComplaintDetail extends Complaint {
  evidence: Evidence;
  suggestion: Evidence["nearest_strong_spot"];
  boundary: [number, number][];
  events: ComplaintEvent[];
}

export interface ComplaintPage {
  items: Complaint[];
  total: number;
  counts: Record<ComplaintStatus, number>;
}

export const STATUS_LABEL: Record<ComplaintStatus, string> = {
  detected: "Detected",
  registered: "Registered",
  acknowledged: "Acknowledged",
  in_progress: "In progress",
  resolved: "Resolved",
  verified: "Verified",
  dismissed: "Dismissed",
};

/** Lifecycle order shown in the stepper (dismissed is an exit, not a step). */
export const LIFECYCLE: ComplaintStatus[] = ["detected", "registered", "acknowledged", "in_progress", "resolved", "verified"];

export const STATUS_STYLE: Record<ComplaintStatus, string> = {
  detected: "bg-violet-500/15 text-violet-700 dark:text-violet-300",
  registered: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  acknowledged: "bg-sky-500/15 text-sky-700 dark:text-sky-300",
  in_progress: "bg-amber-500/15 text-amber-800 dark:text-amber-300",
  resolved: "bg-teal-500/15 text-teal-700 dark:text-teal-300",
  verified: "bg-green-600/15 text-green-700 dark:text-green-300",
  dismissed: "bg-muted text-muted-foreground",
};

/** What an engineer can do next from each status. */
export const NEXT_ACTIONS: Record<ComplaintStatus, { to: ComplaintStatus; label: string; variant?: "default" | "outline" | "destructive" }[]> = {
  detected: [{ to: "registered", label: "Register now" }, { to: "dismissed", label: "Dismiss", variant: "outline" }],
  registered: [{ to: "acknowledged", label: "Acknowledge" }, { to: "in_progress", label: "Start work", variant: "outline" }, { to: "dismissed", label: "Dismiss", variant: "outline" }],
  acknowledged: [{ to: "in_progress", label: "Start work" }, { to: "dismissed", label: "Dismiss", variant: "outline" }],
  in_progress: [{ to: "resolved", label: "Mark resolved" }],
  resolved: [{ to: "verified", label: "Confirm fix" , variant: "outline" }, { to: "registered", label: "Reopen", variant: "outline" }],
  verified: [],
  dismissed: [],
};

export const OPEN: ComplaintStatus[] = ["detected", "registered", "acknowledged", "in_progress", "resolved"];

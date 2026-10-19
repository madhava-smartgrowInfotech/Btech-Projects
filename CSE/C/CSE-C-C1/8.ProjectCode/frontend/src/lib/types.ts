export type Role = "ADMIN" | "VOTER" | "AUDITOR";
export type ElectionStatus = "DRAFT" | "OPEN" | "PAUSED" | "CLOSED";

export interface User {
  id: number;
  username: string;
  display_name: string;
  role: Role;
  email: string | null;
}

export interface Election {
  id: number;
  title: string;
  description: string | null;
  status: ElectionStatus;
  start_time: string;
  end_time: string;
}

export interface ElectionStats extends Election {
  eligible: number;
  votes: number;
  turnout: number;
  candidate_count?: number;
}

export interface Candidate {
  id: number;
  election_id: number;
  name: string;
  party: string | null;
  description: string | null;
  manifesto: string | null;
  is_active: boolean;
}

export interface ChainStatus {
  valid: boolean;
  height?: number;
  last_hash?: string | null;
  reason?: string;
  first_invalid?: number;
  expected?: string;
  actual?: string;
  field?: string;
}

export interface Validator {
  node_id: string;
  public_key: string;
  is_active: boolean;
}

export interface Block {
  block_index: number;
  timestamp: string;
  previous_hash: string;
  merkle_root: string;
  block_hash: string;
  transaction_count: number;
}

export interface Transaction {
  tx_hash: string;
  block_index: number;
  election_id: number;
  ballot_id: string;
  encrypted_payload: string;
  nonce: string;
  timestamp: string;
}

export interface AuditEntry {
  id: number;
  timestamp: string;
  actor: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  details: string | null;
}

export interface BatchStats {
  batch_size?: number;
  total_ops?: number;
  successes?: number;
  fails?: number;
  total_duration?: number;
  throughput?: number;
  mean_ms?: number;
  median_ms?: number;
  p95_ms?: number;
  min_ms?: number;
  max_ms?: number;
  stdev_ms?: number;
}

export interface BenchmarkDetails {
  timestamp?: string;
  voters_count?: number;
  sync?: BatchStats;
  async_batches?: Record<string, BatchStats>;
}

export interface BenchmarkRun {
  id: number;
  timestamp: string;
  total_ops: number;
  sync_duration: number | null;
  async_duration: number | null;
  throughput_sync: number | null;
  throughput_async: number | null;
  mean_latency_ms: number | null;
  p95_latency_ms: number | null;
  details: BenchmarkDetails | null;
}

export interface PublicOverview {
  elections: Election[];
  ledger: { valid: boolean | null; height: number | null };
  votes_cast: number;
  validators: number;
}

export interface AdminOverview {
  total_voters: number;
  total_votes: number;
  turnout: number;
  election_count: number;
  open_count: number;
  chain: ChainStatus;
  validators: Validator[];
  benchmark: BenchmarkRun | null;
  elections: ElectionStats[];
  blocks: Block[];
  audit_logs: AuditEntry[];
}

export interface TallyRow {
  candidate_id: number;
  name: string;
  party: string | null;
  votes: number;
}

export interface TallyResult {
  total_votes: number;
  results: TallyRow[];
}

export interface ElectionDetail {
  election: Election;
  candidates: Candidate[];
  eligible: number;
  votes: number;
  turnout: number;
  results: TallyResult | null;
}

export interface VoterElection extends Election {
  voted: boolean;
  ballot_id: string | null;
  candidate_count: number;
}

export interface VoterElectionDetail {
  election: Election;
  masked_aadhaar: string | null;
  voted: boolean;
  ballot_id: string | null;
  voted_at: string | null;
}

export interface VerifyResult {
  auth_token: string;
  expires_in: number;
  candidates: Candidate[];
}

export interface Receipt {
  ballot_id: string;
  tx_hash: string;
  block_index: number;
  block_hash: string;
}

export interface AuditorOverview {
  chain: ChainStatus;
  validators: Validator[];
  blocks: Block[];
  transactions: Transaction[];
  audit_logs: AuditEntry[];
}

export interface TamperResult {
  tested?: boolean;
  reason?: string;
  detected?: boolean;
  tampered_block?: number;
  expected?: string;
  tampered?: string;
  mismatch_field?: string;
  note?: string;
}

export interface BlockDetail {
  block: Block;
  signatures: Record<string, string>;
  transactions: Transaction[];
  height: number;
}

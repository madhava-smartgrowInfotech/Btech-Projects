/** Phone-probe storage in IndexedDB - shared by the page and the service worker (no window APIs here). */
import { createStore, del, entries, get, getMany, set, setMany } from "idb-keyval";

export interface ReadingPayload {
  client_uuid: string;
  ts: string;
  lat: number;
  lon: number;
  accuracy_m: number | null;
  operator?: string;
  connection_type?: string;
  effective_type?: string;
  downlink_est?: number;
  rtt_est?: number;
  connected: boolean;
  probes_sent: number;
  probes_ok: number;
  latency_ms: number | null;
  jitter_ms: number | null;
  packet_loss: number | null;
  dl_mbps: number | null;
  ul_mbps: number | null;
}

export interface ServerVerdict {
  zone_label: string | null;
  zone_confidence: number | null;
  label_method: string | null;
  radio_estimate: string | null;
  radio_estimate_conf: number | null;
  reasons: string[];
}

export interface ProbeRecord {
  reading: ReadingPayload;
  status: "queued" | "synced" | "rejected";
  provisional: { label: "Strong" | "Weak" | "Dead"; reasons: string[] };
  server?: ServerVerdict;
  operator?: string | null;
  error?: string;
  created: number;
  synced_at?: number;
}

export interface ProbeMeta {
  deviceKey: string;
  deviceId: number;
  deviceName: string;
  userId: number;
}

export interface SyncState {
  lastSyncAt: number | null;
  lastError: string | null;
  lastBatch: { accepted: number; duplicates: number; rejected: number } | null;
  operator: string | null;
  link: string | null;
}

const readings = createStore("signalscout-probe-readings", "readings");
const meta = createStore("signalscout-probe-meta", "meta");
const MAX_KEEP_SYNCED = 1500;

export const probeStore = {
  async put(rec: ProbeRecord) {
    await set(rec.reading.client_uuid, rec, readings);
  },
  async putMany(recs: ProbeRecord[]) {
    await setMany(recs.map((r) => [r.reading.client_uuid, r] as [IDBValidKey, ProbeRecord]), readings);
  },
  async all(): Promise<ProbeRecord[]> {
    const rows = await entries<string, ProbeRecord>(readings);
    return rows.map(([, v]) => v).sort((a, b) => b.created - a.created);
  },
  async queued(limit = 200): Promise<ProbeRecord[]> {
    const rows = await entries<string, ProbeRecord>(readings);
    return rows.map(([, v]) => v).filter((r) => r.status === "queued").sort((a, b) => a.created - b.created).slice(0, limit);
  },
  async getMany(ids: string[]): Promise<(ProbeRecord | undefined)[]> {
    return getMany(ids, readings);
  },
  /** Keep the local log small: drop the oldest synced readings beyond the limit. */
  async prune() {
    const all = await this.all();
    const synced = all.filter((r) => r.status !== "queued");
    await Promise.all(synced.slice(MAX_KEEP_SYNCED).map((r) => del(r.reading.client_uuid, readings)));
  },
  async clear() {
    const all = await entries<string, ProbeRecord>(readings);
    await Promise.all(all.filter(([, v]) => v.status !== "queued").map(([k]) => del(k, readings)));
  },
  getMeta: () => get<ProbeMeta>("device", meta),
  setMeta: (m: ProbeMeta) => set("device", m, meta),
  clearMeta: () => del("device", meta),
  getSync: async (): Promise<SyncState> =>
    (await get<SyncState>("sync", meta)) ?? { lastSyncAt: null, lastError: null, lastBatch: null, operator: null, link: null },
  setSync: (s: SyncState) => set("sync", s, meta),
  getPack: () => get<StrongSpotPack>("pack", meta),
  setPack: (p: StrongSpotPack) => set("pack", p, meta),
};

export interface StrongSpotPack {
  fetched_at: number;
  center: [number, number];
  operator: string | null;
  spots: { lat: number; lon: number; value: number; p_strong: number; target: string }[];
}

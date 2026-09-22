/** Upload queued readings. Runs in the page and in the service worker (Background Sync), so no window APIs. */
import { probeStore, type ProbeRecord, type ServerVerdict } from "./store";

interface IngestResponse {
  accepted: number;
  duplicates: number;
  rejected: number;
  operator: string | null;
  link: string | null;
  results: ({ client_uuid: string; status: "accepted" | "duplicate" | "rejected"; error?: string | null } & ServerVerdict)[];
}

export type FlushOutcome = { sent: number; remaining: number; error?: string; unauthorized?: boolean };

let running: Promise<FlushOutcome> | null = null;

/** Send everything that is queued, 200 at a time. Safe to call often - concurrent calls share one run. */
export function flushQueue(): Promise<FlushOutcome> {
  if (!running) running = doFlush().finally(() => (running = null));
  return running;
}

async function doFlush(): Promise<FlushOutcome> {
  const meta = await probeStore.getMeta();
  if (!meta) return { sent: 0, remaining: (await probeStore.queued(10000)).length, error: "This phone is not registered" };
  let sent = 0;
  for (let round = 0; round < 50; round++) {
    const batch = await probeStore.queued(200);
    if (!batch.length) break;
    let res: Response;
    try {
      res = await fetch("/api/ingest/readings", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Device-Key": meta.deviceKey },
        body: JSON.stringify({ readings: batch.map((r) => r.reading) }),
      });
    } catch {
      return finish(sent, "No connection to SignalScout - will retry");
    }
    if (res.status === 401) return { ...(await finish(sent, "This phone's key is no longer valid - register it again")), unauthorized: true };
    if (!res.ok) return finish(sent, `Upload failed (HTTP ${res.status}) - will retry`);
    const body = (await res.json()) as IngestResponse;
    const byId = new Map(body.results.map((r) => [r.client_uuid, r]));
    const now = Date.now();
    const updated: ProbeRecord[] = batch.map((rec) => {
      const r = byId.get(rec.reading.client_uuid);
      if (!r) return rec;
      if (r.status === "rejected") return { ...rec, status: "rejected", error: r.error ?? "Rejected by the server", synced_at: now };
      return {
        ...rec,
        status: "synced",
        synced_at: now,
        operator: body.operator,
        server: r.status === "accepted"
          ? { zone_label: r.zone_label, zone_confidence: r.zone_confidence, label_method: r.label_method, radio_estimate: r.radio_estimate, radio_estimate_conf: r.radio_estimate_conf, reasons: r.reasons ?? [] }
          : rec.server,
      };
    });
    await probeStore.putMany(updated);
    sent += batch.length;
    const s = await probeStore.getSync();
    await probeStore.setSync({ ...s, lastSyncAt: now, lastError: null, lastBatch: { accepted: body.accepted, duplicates: body.duplicates, rejected: body.rejected },
      operator: body.operator ?? s.operator, link: body.link ?? s.link });
  }
  await probeStore.prune();
  return { sent, remaining: (await probeStore.queued(10000)).length };
}

async function finish(sent: number, error: string): Promise<FlushOutcome> {
  const s = await probeStore.getSync();
  await probeStore.setSync({ ...s, lastError: error });
  return { sent, remaining: (await probeStore.queued(10000)).length, error };
}

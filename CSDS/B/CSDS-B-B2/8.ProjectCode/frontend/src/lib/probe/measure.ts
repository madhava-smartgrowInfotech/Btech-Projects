/** Measurements the phone browser can make: latency probes, download/upload speed, connection hints. */

export interface PingResult {
  sent: number;
  ok: number;
  rttMs: number | null;
  jitterMs: number | null;
}

async function timed<T>(fn: (signal: AbortSignal) => Promise<T>, timeoutMs: number): Promise<{ ms: number; value: T } | null> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  const start = performance.now();
  try {
    const value = await fn(ctrl.signal);
    return { ms: performance.now() - start, value };
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export async function pingProbes(count = 3, timeoutMs = 3000): Promise<PingResult> {
  const rtts: number[] = [];
  for (let i = 0; i < count; i++) {
    const r = await timed(async (signal) => {
      const res = await fetch(`/api/probe/ping?_=${Date.now()}-${i}`, { cache: "no-store", signal });
      if (!res.ok) throw new Error(String(res.status));
      await res.text();
      return true;
    }, timeoutMs);
    if (r) rtts.push(r.ms);
  }
  if (!rtts.length) return { sent: count, ok: 0, rttMs: null, jitterMs: null };
  const sorted = [...rtts].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)]!;
  const diffs = rtts.slice(1).map((v, i) => Math.abs(v - rtts[i]!));
  return { sent: count, ok: rtts.length, rttMs: Math.round(median), jitterMs: diffs.length ? Math.round(diffs.reduce((a, b) => a + b, 0) / diffs.length) : 0 };
}

/** Download test: throughput from the first byte to the last (latency excluded). On very fast links the whole
 *  payload can arrive in one chunk; then total time minus one round trip is used instead. */
export async function downloadTest(deviceKey: string, bytes: number, rttMs: number | null, maxMs = 8000): Promise<{ mbps: number; ms: number; bytes: number } | null> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), maxMs);
  const start = performance.now();
  let received = 0;
  let firstAt = 0;
  let firstChunk = 0;
  try {
    const res = await fetch(`/api/probe/download?bytes=${bytes}&_=${Date.now()}`, { headers: { "X-Device-Key": deviceKey }, cache: "no-store", signal: ctrl.signal });
    if (!res.ok || !res.body) return null;
    const reader = res.body.getReader();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!firstAt) {
        firstAt = performance.now();
        firstChunk = value.length;
      }
      received += value.length;
    }
  } catch {
    /* timed out: use what arrived */
  } finally {
    clearTimeout(timer);
  }
  if (!received) return null;
  const end = performance.now();
  const streamMs = firstAt ? end - firstAt : 0;
  const payload = received - firstChunk;
  if (streamMs >= 50 && payload >= 50_000) return { mbps: (payload * 8) / (streamMs * 1000), ms: end - start, bytes: received };
  const totalMs = Math.max(end - start - (rttMs ?? 0), 5);
  return { mbps: (received * 8) / (totalMs * 1000), ms: end - start, bytes: received };
}

/** Upload test: time to send a random payload, minus one round trip. */
export async function uploadTest(deviceKey: string, bytes: number, rttMs: number | null, maxMs = 8000): Promise<number | null> {
  const buf = new Uint8Array(bytes);
  for (let i = 0; i < bytes; i += 65536) crypto.getRandomValues(buf.subarray(i, Math.min(i + 65536, bytes)));
  const r = await timed(async (signal) => {
    const res = await fetch("/api/probe/upload", { method: "POST", body: buf, headers: { "X-Device-Key": deviceKey, "Content-Type": "application/octet-stream" }, cache: "no-store", signal });
    if (!res.ok) throw new Error(String(res.status));
    return res.json();
  }, maxMs);
  if (!r) return null;
  const ms = Math.max(r.ms - (rttMs ?? 0), 30);
  return (bytes * 8) / (ms * 1000);
}

interface NetInfo {
  type?: string;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
}

export function connectionHints(): NetInfo {
  const c = (navigator as unknown as { connection?: NetInfo }).connection;
  if (!c) return {};
  return { type: c.type, effectiveType: c.effectiveType, downlink: c.downlink, rtt: c.rtt };
}

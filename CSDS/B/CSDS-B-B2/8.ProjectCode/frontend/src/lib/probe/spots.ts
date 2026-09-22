import { api } from "@/lib/api";
import { probeStore, type StrongSpotPack } from "./store";
import type { ProbeRecord } from "./store";

const R = 6371008.8;
const rad = (d: number) => (d * Math.PI) / 180;

export function distance(a: [number, number], b: [number, number]) {
  const dphi = rad(b[0] - a[0]);
  const dl = rad(b[1] - a[1]);
  const h = Math.sin(dphi / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

export function bearing(a: [number, number], b: [number, number]) {
  const y = Math.sin(rad(b[1] - a[1])) * Math.cos(rad(b[0]));
  const x = Math.cos(rad(a[0])) * Math.sin(rad(b[0])) - Math.sin(rad(a[0])) * Math.cos(rad(b[0])) * Math.cos(rad(b[1] - a[1]));
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
export const compass = (b: number) => COMPASS[Math.floor((b + 22.5) / 45) % 8]!;

export interface NearestSpot { lat: number; lon: number; kind: string; d: number }

/** Nearest strong place that works without a connection: the saved pack of predicted strong spots,
 *  or places where this phone itself measured Strong. Spots closer than 25 m are ignored (you are there). */
export function nearestStrong(pos: [number, number], pack: StrongSpotPack | null | undefined, records: ProbeRecord[]): NearestSpot | null {
  const candidates = [
    ...(pack?.spots ?? []).map((s) => ({ lat: s.lat, lon: s.lon, kind: "predicted strong spot" })),
    ...records.filter((r) => (r.server?.zone_label ?? r.provisional.label) === "Strong").map((r) => ({ lat: r.reading.lat, lon: r.reading.lon, kind: "place where you had strong signal" })),
  ];
  let best: NearestSpot | null = null;
  for (const c of candidates) {
    const d = distance(pos, [c.lat, c.lon]);
    if (d > 25 && (!best || d < best.d)) best = { ...c, d };
  }
  return best;
}

/** Downloads predicted strong spots around the phone for offline use when the saved pack is old or far away. */
export async function refreshPack(pos: [number, number], operator: string | null, pack: StrongSpotPack | null | undefined): Promise<StrongSpotPack | null> {
  const stale = !pack || Date.now() - pack.fetched_at > 30 * 60_000 || distance(pack.center, pos) > 1000;
  if (!stale) return pack ?? null;
  const params = { lat: pos[0], lon: pos[1], radius_m: 2500, ...(operator ? { operator } : {}) };
  const area = (await api.get<Omit<StrongSpotPack, "fetched_at">>("/api/suggest/area", { params })).data;
  const next = { ...area, fetched_at: Date.now() };
  await probeStore.setPack(next);
  return next;
}

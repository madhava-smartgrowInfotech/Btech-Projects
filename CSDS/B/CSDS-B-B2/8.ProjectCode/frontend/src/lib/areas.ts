import type { HexCollection } from "./coverage";

/** A group of zones that lie together (a town or city). Zones in grid squares of about 30 km that touch are one area. */
export interface Area {
  key: string;
  zones: number;
  bounds: [[number, number], [number, number]];
  center: [number, number];
  lastTs: string;
  /** latest reading from a real phone or ESP32 node (not the sample or the simulator), if any */
  lastRealTs: string | null;
  sampleOnly: boolean;
}

const STEP = 0.3; // degrees

export function groupAreas(features: HexCollection["features"]): Area[] {
  if (!features.length) return [];
  const cellOf = (lat: number, lon: number) => `${Math.floor(lat / STEP)}:${Math.floor(lon / STEP)}`;
  const parent = new Map<string, string>();
  const find = (k: string): string => {
    let r = k;
    while (parent.get(r) !== r) r = parent.get(r)!;
    parent.set(k, r);
    return r;
  };
  for (const f of features) {
    const k = cellOf(f.properties.center[0], f.properties.center[1]);
    if (!parent.has(k)) parent.set(k, k);
  }
  for (const k of [...parent.keys()]) {
    const [i, j] = k.split(":").map(Number) as [number, number];
    for (let di = -1; di <= 1; di++)
      for (let dj = -1; dj <= 1; dj++) {
        const n = `${i + di}:${j + dj}`;
        if (parent.has(n)) {
          const a = find(k), b = find(n);
          if (a !== b) parent.set(a < b ? b : a, a < b ? a : b);
        }
      }
  }
  const groups = new Map<string, Area>();
  for (const f of features) {
    const [lat, lon] = f.properties.center;
    const key = find(cellOf(lat, lon));
    const g = groups.get(key);
    const sample = f.properties.sources.every((s) => s === "sample_dataset");
    const real = f.properties.sources.some((s) => s === "phone" || s === "esp32") ? f.properties.last_ts : null;
    if (!g) {
      groups.set(key, { key, zones: 1, bounds: [[lat, lon], [lat, lon]], center: [lat, lon], lastTs: f.properties.last_ts, lastRealTs: real, sampleOnly: sample });
    } else {
      g.zones += 1;
      g.bounds = [[Math.min(g.bounds[0][0], lat), Math.min(g.bounds[0][1], lon)], [Math.max(g.bounds[1][0], lat), Math.max(g.bounds[1][1], lon)]];
      if (f.properties.last_ts > g.lastTs) g.lastTs = f.properties.last_ts;
      if (real && (!g.lastRealTs || real > g.lastRealTs)) g.lastRealTs = real;
      g.sampleOnly = g.sampleOnly && sample;
    }
  }
  for (const g of groups.values()) g.center = [(g.bounds[0][0] + g.bounds[1][0]) / 2, (g.bounds[0][1] + g.bounds[1][1]) / 2];
  // where real devices measured most recently comes first (that is where people are working now); then the largest area
  return [...groups.values()].sort((a, b) => {
    if (a.lastRealTs || b.lastRealTs) {
      if (!a.lastRealTs) return 1;
      if (!b.lastRealTs) return -1;
      if (a.lastRealTs !== b.lastRealTs) return a.lastRealTs < b.lastRealTs ? 1 : -1;
    }
    return b.zones - a.zones;
  });
}

export const areaLabel = (a: Area) => `${a.sampleOnly ? "Sample data" : "Area"} near ${a.center[0].toFixed(2)}, ${a.center[1].toFixed(2)} · ${a.zones} zone${a.zones === 1 ? "" : "s"}`;

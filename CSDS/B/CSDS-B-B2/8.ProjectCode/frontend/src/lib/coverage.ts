import { useEffect, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { api, TOKEN_KEY } from "./api";
import { safeStorage } from "./utils";
import type { ZoneLabel } from "./zones";

export interface CoverageFilters {
  operator: string | null;
  days: number | null;
  hours: [number, number] | null;
  sources: string[];
  includeWifi: boolean;
}

export const DEFAULT_FILTERS: CoverageFilters = { operator: null, days: null, hours: null, sources: [], includeWifi: false };

export function filterParams(f: CoverageFilters): Record<string, string | number | boolean> {
  const p: Record<string, string | number | boolean> = { tz_offset_min: -new Date().getTimezoneOffset() };
  if (f.operator) p.operator = f.operator;
  if (f.days) p.days = f.days;
  if (f.hours) {
    p.hour_from = f.hours[0];
    p.hour_to = f.hours[1];
  }
  if (f.sources.length) p.sources = f.sources.join(",");
  if (f.includeWifi) p.include_wifi = true;
  return p;
}

export interface CoverageSummary {
  operators: { name: string; readings: number }[];
  sources: { name: string; readings: number }[];
  first_ts: string | null;
  last_ts: string | null;
  bounds: [[number, number], [number, number]] | null;
  total: number;
  sample_data: { state: string; readings: number };
}

export interface HexProps {
  cell: string;
  n: number;
  strong: number;
  weak: number;
  dead: number;
  label: ZoneLabel;
  bad_share: number;
  confidence: number | null;
  median_rsrp: number | null;
  median_latency: number | null;
  median_dl: number | null;
  median_wifi_rssi: number | null;
  last_ts: string;
  sources: string[];
  operators: Record<string, { n: number; label: ZoneLabel }>;
  center: [number, number];
}

export interface HexCollection {
  type: "FeatureCollection";
  features: { type: "Feature"; geometry: { type: "Polygon"; coordinates: number[][][] }; properties: HexProps }[];
  resolution: number;
  readings: number;
}

export interface LivePoint {
  id: number;
  ts: string;
  lat: number;
  lon: number;
  label: ZoneLabel | null;
  confidence: number | null;
  operator: string;
  source: string;
  rsrp?: number | null;
  latency_ms?: number | null;
  dl_mbps?: number | null;
  wifi_rssi?: number | null;
  fresh?: boolean;
}

export interface NodeInfo {
  id: number;
  name: string;
  kind: string;
  lat: number;
  lon: number;
  online: boolean;
  network_name: string | null;
  last_seen_at: string | null;
  label: ZoneLabel | null;
  wifi_rssi: number | null;
  latency_ms: number | null;
}

export const useCoverageSummary = () =>
  useQuery({ queryKey: ["coverage-summary"], queryFn: async () => (await api.get<CoverageSummary>("/api/coverage/summary")).data, refetchInterval: 60_000 });

export const useHexes = (f: CoverageFilters) =>
  useQuery({
    queryKey: ["coverage-hex", f],
    queryFn: async () => (await api.get<HexCollection>("/api/coverage/hex", { params: filterParams(f) })).data,
    placeholderData: keepPreviousData,
    refetchInterval: 60_000,
  });

export const useHeat = (f: CoverageFilters, enabled: boolean) =>
  useQuery({
    queryKey: ["coverage-heat", f],
    enabled,
    queryFn: async () => (await api.get<{ points: [number, number, number][] }>("/api/coverage/heat", { params: { ...filterParams(f), mode: "problems" } })).data,
    placeholderData: keepPreviousData,
  });

export const usePoints = (f: CoverageFilters, enabled: boolean) =>
  useQuery({
    queryKey: ["coverage-points", f],
    enabled,
    queryFn: async () => (await api.get<LivePoint[]>("/api/coverage/points", { params: { ...filterParams(f), limit: 400 } })).data,
    placeholderData: keepPreviousData,
  });

export const useNodes = (enabled: boolean) =>
  useQuery({ queryKey: ["coverage-nodes"], enabled, queryFn: async () => (await api.get<NodeInfo[]>("/api/coverage/nodes")).data, refetchInterval: 30_000 });

/** Live events over Server-Sent Events; reconnects automatically. */
export function useLiveStream(enabled: boolean, onReadings?: (pts: LivePoint[]) => void) {
  const [connected, setConnected] = useState(false);
  const cb = useRef(onReadings);
  cb.current = onReadings;
  useEffect(() => {
    if (!enabled || typeof EventSource === "undefined") return;
    const token = safeStorage.get(TOKEN_KEY);
    if (!token) return;
    const es = new EventSource(`/api/coverage/stream?access_token=${encodeURIComponent(token)}`);
    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.addEventListener("readings", (e) => {
      try {
        cb.current?.(JSON.parse((e as MessageEvent).data) as LivePoint[]);
      } catch {
        /* ignore malformed event */
      }
    });
    return () => {
      es.close();
      setConnected(false);
    };
  }, [enabled]);
  return connected;
}

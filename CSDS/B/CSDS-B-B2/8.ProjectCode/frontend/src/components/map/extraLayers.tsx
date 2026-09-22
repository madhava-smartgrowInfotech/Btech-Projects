import { useEffect, useRef, useState } from "react";
import { CircleMarker, Polyline, Rectangle, Tooltip, useMap, useMapEvents } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { STATUS_LABEL, type Complaint, type ComplaintPage } from "@/lib/complaints";
import { ZONE_COLOR } from "@/lib/zones";

const PIN: Record<string, string> = { detected: "#7c5cff", registered: "#e11d48", acknowledged: "#0284c7", in_progress: "#d97706", resolved: "#0d9488" };

export function ComplaintsLayer() {
  const navigate = useNavigate();
  const q = useQuery({
    queryKey: ["complaints", "map-layer"],
    queryFn: async () => (await api.get<ComplaintPage>("/api/complaints", { params: { status: "detected,registered,acknowledged,in_progress,resolved", limit: 300 } })).data,
    refetchInterval: 30_000,
  });
  return (
    <>
      {q.data?.items.map((c: Complaint) => (
        <CircleMarker key={c.id} center={[c.lat, c.lon]} radius={9} pathOptions={{ color: "#fff", weight: 2.5, fillColor: PIN[c.status] ?? "#8d8c87", fillOpacity: 1 }}
          eventHandlers={{ click: () => navigate(`/app/complaints/${c.id}`) }}>
          <Tooltip direction="top">{c.ref_code} · {STATUS_LABEL[c.status]} · {c.operator} - click to open</Tooltip>
        </CircleMarker>
      ))}
    </>
  );
}

interface Cell { lat: number; lon: number; value: number; sd: number; p_strong: number }
interface Surface { cells: Cell[]; target: string | null; operator: string | null; step_m?: number; unit?: string }

/** Chance of strong signal from the Gaussian Process, around the map centre (single-hue ramp: darker = more likely). */
export function PredictedLayer({ operator, onInfo }: { operator: string | null; onInfo: (s: { operator: string | null; target: string | null; cells: number } | null) => void }) {
  const map = useMap();
  const [center, setCenter] = useState<[number, number]>(() => [map.getCenter().lat, map.getCenter().lng]);
  const timer = useRef<number>();
  useMapEvents({
    moveend: () => {
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setCenter([map.getCenter().lat, map.getCenter().lng]), 400);
    },
  });
  const key: [number, number] = [Math.round(center[0] * 200) / 200, Math.round(center[1] * 200) / 200];
  const q = useQuery({
    queryKey: ["predicted", key, operator],
    queryFn: async () => (await api.get<Surface>("/api/coverage/predicted", { params: { lat: key[0], lon: key[1], radius_m: 1500, ...(operator ? { operator } : {}) } })).data,
    staleTime: 60_000,
  });
  useEffect(() => {
    onInfo(q.data ? { operator: q.data.operator, target: q.data.target, cells: q.data.cells.length } : null);
  }, [q.data, onInfo]);
  if (!q.data?.cells.length) return null;
  const half = (q.data.step_m ?? 40) / 2;
  const dLat = half / 111_320;
  return (
    <>
      {q.data.cells.map((c, i) => {
        const dLon = half / (111_320 * Math.cos((c.lat * Math.PI) / 180));
        return (
          <Rectangle key={i} bounds={[[c.lat - dLat, c.lon - dLon], [c.lat + dLat, c.lon + dLon]]}
            pathOptions={{ stroke: false, fillColor: "#184f95", fillOpacity: 0.08 + 0.55 * c.p_strong }} />
        );
      })}
    </>
  );
}

export function SuggestionLayer({ from, to }: { from: [number, number]; to: [number, number] }) {
  return (
    <>
      <Polyline positions={[from, to]} pathOptions={{ color: "#2a78d6", weight: 3, dashArray: "8 8" }} />
      <CircleMarker center={to} radius={10} pathOptions={{ color: "#fff", weight: 3, fillColor: ZONE_COLOR.Strong, fillOpacity: 1 }}>
        <Tooltip permanent direction="top" offset={[0, -8]}>Better signal here</Tooltip>
      </CircleMarker>
    </>
  );
}

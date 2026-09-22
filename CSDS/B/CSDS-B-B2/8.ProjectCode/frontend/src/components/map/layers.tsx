import { useEffect, useMemo, useRef } from "react";
import { CircleMarker, GeoJSON, Marker, Popup, Tooltip, useMap } from "react-leaflet";
import type { Feature, GeoJsonObject } from "geojson";
import L from "./leaflet-setup";
import type { HexCollection, HexProps, LivePoint, NodeInfo } from "@/lib/coverage";
import { timeAgo } from "@/lib/utils";
import { ZONE_COLOR, isZone } from "@/lib/zones";

export function HexLayer({ data, selected, onSelect }: { data: HexCollection; selected: string | null; onSelect: (p: HexProps) => void }) {
  const key = useMemo(() => `${data.features.length}-${data.readings}-${selected}`, [data, selected]);
  return (
    <GeoJSON
      key={key}
      data={data as unknown as GeoJsonObject}
      style={(f?: Feature) => {
        const p = f?.properties as HexProps;
        const color = ZONE_COLOR[p.label];
        const isSel = p.cell === selected;
        return {
          color: isSel ? "#111827" : color,
          weight: isSel ? 3 : 1,
          opacity: 0.9,
          fillColor: color,
          fillOpacity: 0.28 + 0.34 * Math.min(1, p.n / 40),
        };
      }}
      onEachFeature={(f, layer) => {
        const p = f.properties as HexProps;
        layer.bindTooltip(`<strong>${p.label}</strong> · ${p.n} reading${p.n === 1 ? "" : "s"}`, { sticky: true, direction: "top" });
        layer.on({
          click: () => onSelect(p),
          mouseover: (e) => (e.target as L.Path).setStyle({ weight: 3 }),
          mouseout: (e) => (e.target as L.Path).setStyle({ weight: p.cell === selected ? 3 : 1 }),
        });
      }}
    />
  );
}

export function LivePointsLayer({ points }: { points: LivePoint[] }) {
  return (
    <>
      {points.map((p) =>
        isZone(p.label) ? (
          <CircleMarker
            key={p.id}
            center={[p.lat, p.lon]}
            radius={p.fresh ? 7 : 4.5}
            pathOptions={{ color: "#ffffff", weight: 1.5, fillColor: ZONE_COLOR[p.label], fillOpacity: 0.95, className: p.fresh ? "live-pulse" : undefined }}
          >
            <Tooltip direction="top">
              <span className="text-xs">
                <strong>{p.label}</strong>
                {p.confidence != null && ` ${Math.round(p.confidence * 100)}%`} · {p.operator} · {timeAgo(p.ts)}
                {p.latency_ms != null && <><br />{Math.round(p.latency_ms)} ms{p.dl_mbps != null && ` · ${p.dl_mbps.toFixed(1)} Mbps`}</>}
                {p.rsrp != null && <><br />RSRP {Math.round(p.rsrp)} dBm</>}
                {p.wifi_rssi != null && <><br />Wi-Fi {Math.round(p.wifi_rssi)} dBm</>}
              </span>
            </Tooltip>
          </CircleMarker>
        ) : null,
      )}
    </>
  );
}

function nodeIcon(n: NodeInfo) {
  const color = n.online && isZone(n.label) ? ZONE_COLOR[n.label] : "#8d8c87";
  return L.divIcon({
    className: "",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    html: `<div style="width:30px;height:30px;border-radius:9px;background:${color};border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><circle cx="12" cy="20" r="1"/></svg></div>`,
  });
}

export function NodesLayer({ nodes }: { nodes: NodeInfo[] }) {
  return (
    <>
      {nodes.map((n) => (
        <Marker key={n.id} position={[n.lat, n.lon]} icon={nodeIcon(n)} title={`${n.name}: ${n.online ? "online" : "offline"}`} alt={n.name}>
          <Popup>
            <div className="min-w-[180px] text-xs leading-relaxed">
              <p className="text-sm font-semibold">{n.name}</p>
              <p>{n.network_name ?? "Wi-Fi link"} · {n.kind === "simulator" ? "simulated node" : "ESP32 node"}</p>
              <p>{n.online ? "Online" : "Offline"} · last report {timeAgo(n.last_seen_at)}</p>
              {n.label && <p>Link: <strong>{n.label}</strong>{n.wifi_rssi != null && ` · ${Math.round(n.wifi_rssi)} dBm`}{n.latency_ms != null && ` · ${Math.round(n.latency_ms)} ms`}</p>}
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
}

/** Fit the map to the data once, and again whenever `fitKey` changes. */
export function FitBounds({ bounds, fitKey }: { bounds: L.LatLngBoundsExpression | null; fitKey: string }) {
  const map = useMap();
  const done = useRef<string | null>(null);
  useEffect(() => {
    if (!bounds || done.current === fitKey) return;
    done.current = fitKey;
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16, animate: false });
  }, [bounds, fitKey, map]);
  return null;
}

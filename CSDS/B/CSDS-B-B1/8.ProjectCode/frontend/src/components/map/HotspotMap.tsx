import "leaflet/dist/leaflet.css";

import { CircleMarker, MapContainer, Tooltip } from "react-leaflet";

import { BaseTiles, CITY_CENTER } from "@/components/map/LocationPicker";
import { PRIORITY_COLOR } from "@/components/domain/Badges";
import type { Hotspots } from "@/lib/types";

/** Light-to-strong ramp (cool -> violet -> magenta) used for ward circles and the legend. */
export const HEAT = ["#67E8F9", "#38BDF8", "#7C8CFF", "#7C5CFF", "#C45CF2", "#F472B6"];

export default function HotspotMap({ data, showPoints }: { data: Hotspots; showPoints: boolean }) {
  const max = Math.max(...data.wards.map((w) => w.total), 1);
  const step = (v: number) => HEAT[Math.min(HEAT.length - 1, Math.floor((v / max) * (HEAT.length - 1) + 0.0001))];
  return (
    <MapContainer center={CITY_CENTER} zoom={11} className="h-full w-full" scrollWheelZoom={false}>
      <BaseTiles />
      {!showPoints &&
        data.wards.map((w) => (
          <CircleMarker
            key={w.ward}
            center={[w.lat, w.lng]}
            radius={6 + 22 * Math.sqrt(w.total / max)}
            pathOptions={{ color: "#fff", weight: 2, fillColor: step(w.total), fillOpacity: 0.85 }}
          >
            <Tooltip>
              <b>{w.ward}</b>
              <br />
              {w.total} complaints · {w.open} open · {w.critical_or_high} high/critical
              <br />
              Most common: {w.top_category} ({w.top_count})
            </Tooltip>
          </CircleMarker>
        ))}
      {showPoints &&
        data.points.map((p) => (
          <CircleMarker key={p.id} center={[p.lat, p.lng]} radius={5} pathOptions={{ color: "#fff", weight: 1.5, fillColor: PRIORITY_COLOR[p.priority], fillOpacity: 1 }}>
            <Tooltip>
              <b>{p.tracking_id}</b> · {p.priority}
              <br />
              {p.category} · {p.status}
            </Tooltip>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}

import "leaflet/dist/leaflet.css";

import { LocateFixed } from "lucide-react";
import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";

import { Button } from "@/components/ui/Button";

export interface Point {
  lat: number;
  lng: number;
}

export const CITY_CENTER: [number, number] = [12.9716, 77.5946]; // sample city: Bengaluru
const TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION = "&copy; OpenStreetMap contributors";

export function BaseTiles() {
  return <TileLayer url={TILES} attribution={ATTRIBUTION} />;
}

function ClickHandler({ onPick }: { onPick: (p: Point) => void }) {
  useMapEvents({ click: (e) => onPick({ lat: e.latlng.lat, lng: e.latlng.lng }) });
  return null;
}

function FlyTo({ point }: { point: Point | null }) {
  const map = useMap();
  useEffect(() => {
    if (point) map.flyTo([point.lat, point.lng], Math.max(map.getZoom(), 15), { duration: 0.5 });
  }, [point, map]);
  return null;
}

/** Tap the map (or use the device location) to pin where the problem is. */
export default function LocationPicker({ value, onChange }: { value: Point | null; onChange: (p: Point | null) => void }) {
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState("");
  const [flyTarget, setFlyTarget] = useState<Point | null>(null);

  function locate() {
    if (!navigator.geolocation) return setGeoError("Location is not available in this browser - tap the map instead.");
    setLocating(true);
    setGeoError("");
    navigator.geolocation.getCurrentPosition(
      (p) => {
        const pt = { lat: p.coords.latitude, lng: p.coords.longitude };
        onChange(pt);
        setFlyTarget(pt);
        setLocating(false);
      },
      () => {
        setGeoError("Could not get your location - tap the map instead.");
        setLocating(false);
      },
      { timeout: 10_000 },
    );
  }

  return (
    <div>
      <div className="h-72 overflow-hidden rounded-2xl border border-[var(--glass-border)]">
        <MapContainer center={CITY_CENTER} zoom={12} className="h-full w-full" scrollWheelZoom>
          <BaseTiles />
          <ClickHandler onPick={onChange} />
          <FlyTo point={flyTarget} />
          {value && <CircleMarker center={[value.lat, value.lng]} radius={9} pathOptions={{ color: "#fff", weight: 2, fillColor: "#F43F5E", fillOpacity: 1 }} />}
        </MapContainer>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <Button type="button" variant="secondary" size="sm" magnetic={false} onClick={locate} loading={locating}>
          {!locating && <LocateFixed />} {locating ? "Locating…" : "Use my location"}
        </Button>
        {value ? (
          <>
            <span>
              Pinned at {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
            </span>
            <Button type="button" variant="ghost" size="sm" magnetic={false} onClick={() => onChange(null)}>
              Clear pin
            </Button>
          </>
        ) : (
          <span>Tap the map to pin where the problem is.</span>
        )}
        {geoError && (
          <span role="alert" className="text-danger">
            {geoError}
          </span>
        )}
      </div>
    </div>
  );
}

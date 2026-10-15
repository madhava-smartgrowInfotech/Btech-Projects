import "leaflet/dist/leaflet.css";

import { CircleMarker, MapContainer } from "react-leaflet";

import { BaseTiles } from "@/components/map/LocationPicker";

/** Read-only map with a single pin (complaint detail). */
export default function PinMap({ lat, lng }: { lat: number; lng: number }) {
  return (
    <MapContainer center={[lat, lng]} zoom={15} className="h-full w-full" scrollWheelZoom={false}>
      <BaseTiles />
      <CircleMarker center={[lat, lng]} radius={8} pathOptions={{ color: "#fff", weight: 2, fillColor: "#F43F5E", fillOpacity: 1 }} />
    </MapContainer>
  );
}

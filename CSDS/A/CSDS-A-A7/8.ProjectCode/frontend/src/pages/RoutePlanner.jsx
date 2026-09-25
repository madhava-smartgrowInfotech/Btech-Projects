import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Polyline, CircleMarker, Circle, Popup, useMapEvents } from "react-leaflet";
import { Navigation, LocateFixed } from "lucide-react";
import "leaflet/dist/leaflet.css";
import api from "../api";
import { Loading, ErrorMessage } from "../components/StatusMessage";

const TIER_COLOR = { low: "#22c55e", medium: "#f59e0b", high: "#ef4444" };
const ROUTE_COLORS = ["#22c55e", "#64748b", "#94a3b8"]; // safest = green, others = grey

function ClickPicker({ onPick }) {
  useMapEvents({
    click(e) {
      onPick([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

export default function RoutePlanner() {
  const [origin, setOrigin] = useState(null);
  const [dest, setDest] = useState(null);
  const [pickMode, setPickMode] = useState("origin");
  const [areas, setAreas] = useState([]);
  const [routes, setRoutes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const center = origin || [20.5937, 78.9629]; // India centroid fallback

  useEffect(() => {
    api.get("/risk/areas").then((res) => setAreas(res.data)).catch(() => {});
  }, []);

  function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      setOrigin([pos.coords.latitude, pos.coords.longitude]);
      setPickMode("dest");
    });
  }

  function handlePick(latlng) {
    if (pickMode === "origin") {
      setOrigin(latlng);
      setPickMode("dest");
    } else {
      setDest(latlng);
    }
  }

  async function planRoute() {
    if (!origin || !dest) return;
    setError("");
    setLoading(true);
    setRoutes(null);
    try {
      const res = await api.post("/routes/plan", {
        origin_lat: origin[0], origin_lng: origin[1],
        dest_lat: dest[0], dest_lng: dest[1],
      });
      setRoutes(res.data.routes);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not plan a route");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Safe Route planner</h1>
        <p className="text-sm text-slate-400">
          {pickMode === "origin" ? "Tap the map to set your start point" : "Now tap to set your destination"}
        </p>
      </div>

      <div className="flex gap-2">
        <button onClick={useMyLocation} className="flex items-center gap-1 text-sm bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
          <LocateFixed size={16} /> Use my location
        </button>
        <button
          onClick={planRoute}
          disabled={!origin || !dest || loading}
          className="flex items-center gap-1 text-sm bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-lg px-3 py-2 ml-auto"
        >
          <Navigation size={16} /> {loading ? "Planning..." : "Plan safest route"}
        </button>
      </div>

      <ErrorMessage message={error} />

      <div className="h-72 rounded-xl overflow-hidden border border-slate-800">
        <MapContainer center={center} zoom={origin ? 12 : 5} className="h-full w-full">
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickPicker onPick={handlePick} />
          {areas.map((a, i) => (
            <Circle
              key={i}
              center={[a.lat, a.lng]}
              radius={8000}
              pathOptions={{ color: TIER_COLOR[a.risk_tier], fillOpacity: 0.15, weight: 1 }}
            >
              <Popup>{a.district}, {a.state} - {a.risk_tier} risk</Popup>
            </Circle>
          ))}
          {origin && <CircleMarker center={origin} radius={8} pathOptions={{ color: "#38bdf8" }} />}
          {dest && <CircleMarker center={dest} radius={8} pathOptions={{ color: "#f472b6" }} />}
          {routes?.map((r) => (
            <Polyline
              key={r.index}
              positions={r.coordinates}
              pathOptions={{
                color: r.recommended ? ROUTE_COLORS[0] : ROUTE_COLORS[1],
                weight: r.recommended ? 5 : 3,
                opacity: r.recommended ? 0.95 : 0.55,
              }}
            />
          ))}
        </MapContainer>
      </div>

      {loading && <Loading label="Scoring routes by area risk..." />}

      {routes && (
        <div className="space-y-2">
          {routes.map((r) => (
            <div
              key={r.index}
              className={`rounded-xl p-3 border ${
                r.recommended ? "border-green-600 bg-green-950/30" : "border-slate-800 bg-slate-900"
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium">
                  {r.recommended ? "Recommended - safest route" : `Alternative route`}
                </span>
                <span className="text-sm text-slate-400">
                  {(r.distance_m / 1000).toFixed(1)} km - {Math.round(r.duration_s / 60)} min
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Risk score {r.risk_score} - tiers passed through: low {r.risk_tiers.low}, medium {r.risk_tiers.medium}, high {r.risk_tiers.high}
                {r.is_night && " - night-time weighting applied"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker, Polyline } from "react-leaflet";
import { Shield, Radio } from "lucide-react";
import "leaflet/dist/leaflet.css";
import api, { wsUrl } from "../api";
import { Loading, ErrorMessage } from "../components/StatusMessage";

export default function GuardianTrack() {
  const { token } = useParams();
  const [info, setInfo] = useState(null);
  const [path, setPath] = useState([]);
  const [pos, setPos] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    api
      .get(`/track/${token}`)
      .then((res) => {
        setInfo(res.data);
        setStatus(res.data.status);
        if (res.data.last_lat != null) setPos([res.data.last_lat, res.data.last_lng]);
        setPath(res.data.path.map((p) => [p.lat, p.lng]));
      })
      .catch(() => setError("This tracking link is invalid or has expired"));
  }, [token]);

  useEffect(() => {
    if (!info) return;
    const ws = new WebSocket(wsUrl(`/ws/track/${token}`));
    wsRef.current = ws;
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type === "location") {
        setPos([msg.lat, msg.lng]);
        setPath((prev) => [...prev, [msg.lat, msg.lng]]);
      } else if (msg.type === "cancelled") {
        setStatus("cancelled");
      }
    };
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [info, token]);

  if (error) return <div className="min-h-screen flex items-center justify-center p-6"><ErrorMessage message={error} /></div>;
  if (!info) return <div className="min-h-screen flex items-center justify-center"><Loading label="Loading tracking page..." /></div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 space-y-4 max-w-2xl mx-auto">
      <div className="flex items-center gap-2 text-brand-400 font-bold text-lg">
        <Shield size={22} /> SHEGUARD - Live tracking
      </div>

      <div className={`rounded-xl p-4 border ${status === "active" ? "border-red-800 bg-red-950/40" : "border-slate-800 bg-slate-900"}`}>
        <div className="font-medium">{info.user_name} {status === "active" ? "may need help" : "- session ended"}</div>
        <div className="text-xs text-slate-400 flex items-center gap-1 mt-1">
          {status === "active" && <Radio size={12} className="text-red-400 animate-pulse" />}
          Status: {status} - started {new Date(info.started_at).toLocaleString()}
        </div>
      </div>

      <div className="h-96 rounded-xl overflow-hidden border border-slate-800">
        <MapContainer center={pos || [20.5937, 78.9629]} zoom={pos ? 15 : 5} className="h-full w-full">
          <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {path.length > 1 && <Polyline positions={path} pathOptions={{ color: "#ec4899" }} />}
          {pos && <CircleMarker center={pos} radius={10} pathOptions={{ color: "#ef4444" }} />}
        </MapContainer>
      </div>

      <p className="text-xs text-slate-500 text-center">
        This is a read-only link shared by {info.user_name}. If this is a genuine emergency, contact local
        emergency services immediately.
      </p>
    </div>
  );
}

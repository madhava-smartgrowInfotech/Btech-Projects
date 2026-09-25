import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";
import { Camera, Mic, Square, Copy, XCircle, CheckCircle2 } from "lucide-react";
import "leaflet/dist/leaflet.css";
import api from "../api";
import { Loading, ErrorMessage } from "../components/StatusMessage";

export default function EmergencySession() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [pos, setPos] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const watchIdRef = useRef(null);
  const lastPushRef = useRef(0);
  const mediaRecorderRef = useRef(null);
  const fileInputRef = useRef(null);

  async function loadSession() {
    try {
      const res = await api.get(`/sos/${sessionId}`);
      setSession(res.data);
    } catch (err) {
      setError("Session not found");
    }
  }

  async function loadEvidence() {
    try {
      const res = await api.get(`/sos/${sessionId}/evidence`);
      setEvidence(res.data);
    } catch {
      // non-fatal
    }
  }

  useEffect(() => {
    loadSession();
    loadEvidence();

    if (navigator.geolocation) {
      watchIdRef.current = navigator.geolocation.watchPosition(
        (p) => {
          const coords = [p.coords.latitude, p.coords.longitude];
          setPos(coords);
          const now = Date.now();
          if (now - lastPushRef.current > 4000) {
            lastPushRef.current = now;
            api.post(`/sos/${sessionId}/location`, { lat: coords[0], lng: coords[1] }).catch(() => {});
          }
        },
        () => {},
        { enableHighAccuracy: true, maximumAge: 2000 }
      );
    }
    return () => {
      if (watchIdRef.current != null) navigator.geolocation.clearWatch(watchIdRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  async function uploadEvidence(kind, blob, filename) {
    const form = new FormData();
    form.append("kind", kind);
    if (pos) {
      form.append("lat", pos[0]);
      form.append("lng", pos[1]);
    }
    form.append("file", blob, filename);
    try {
      await api.post(`/sos/${sessionId}/evidence`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      loadEvidence();
    } catch (err) {
      setError("Could not upload evidence");
    }
  }

  function handlePhotoPick(e) {
    const file = e.target.files?.[0];
    if (file) uploadEvidence("photo", file, file.name);
    e.target.value = "";
  }

  async function toggleAudioRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const chunks = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: "audio/webm" });
        uploadEvidence("audio", blob, "clip.webm");
        setRecording(false);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      setError("Microphone access denied or unavailable");
    }
  }

  async function cancelSession() {
    setCancelling(true);
    try {
      await api.post(`/sos/${sessionId}/cancel`);
      navigate("/home");
    } catch {
      setError("Could not cancel session");
    } finally {
      setCancelling(false);
    }
  }

  if (!session && !error) return <Loading label="Loading session..." />;

  const trackingUrl = session ? `${window.location.origin}/track/${session.share_token}` : "";

  return (
    <div className="space-y-4">
      <div className="bg-red-950/40 border border-red-800 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold text-red-300">
              Emergency session {session?.status === "active" ? "active" : session?.status}
            </div>
            <div className="text-xs text-slate-400">Trigger: {session?.trigger}</div>
          </div>
          {session?.status === "active" && (
            <button
              onClick={cancelSession}
              disabled={cancelling}
              className="flex items-center gap-1 text-sm bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg px-3 py-1.5"
            >
              <XCircle size={16} /> {cancelling ? "Cancelling..." : "Cancel"}
            </button>
          )}
        </div>
      </div>

      <ErrorMessage message={error} />

      <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-3 text-sm">
        <span className="truncate flex-1 text-slate-400">{trackingUrl}</span>
        <button
          onClick={() => navigator.clipboard?.writeText(trackingUrl)}
          className="text-brand-400 flex items-center gap-1 shrink-0"
        >
          <Copy size={14} /> Copy link
        </button>
      </div>

      <div className="h-64 rounded-xl overflow-hidden border border-slate-800">
        <MapContainer center={pos || [20.5937, 78.9629]} zoom={pos ? 15 : 5} className="h-full w-full">
          <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {pos && <CircleMarker center={pos} radius={9} pathOptions={{ color: "#ef4444" }} />}
        </MapContainer>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center gap-1 bg-slate-900 border border-slate-800 rounded-xl py-4"
        >
          <Camera size={22} className="text-brand-400" />
          <span className="text-sm">Capture photo</span>
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" capture="environment" hidden onChange={handlePhotoPick} />

        <button
          onClick={toggleAudioRecording}
          className="flex flex-col items-center gap-1 bg-slate-900 border border-slate-800 rounded-xl py-4"
        >
          {recording ? <Square size={22} className="text-red-400 animate-pulse" /> : <Mic size={22} className="text-brand-400" />}
          <span className="text-sm">{recording ? "Stop recording" : "Record audio"}</span>
        </button>
      </div>

      {evidence.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-slate-400">Evidence captured</h2>
          {evidence.map((e) => (
            <div key={e.id} className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm">
              <CheckCircle2 size={16} className="text-green-500 shrink-0" />
              <span className="capitalize">{e.kind}</span>
              <span className="text-slate-500 text-xs truncate">sha256:{e.sha256.slice(0, 16)}...</span>
              <span className="text-slate-600 text-xs ml-auto">{new Date(e.captured_at).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

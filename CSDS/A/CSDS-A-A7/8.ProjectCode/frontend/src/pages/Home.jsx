import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, Mic, MicOff } from "lucide-react";
import api from "../api";
import { useAuth } from "../AuthContext";
import { ErrorMessage } from "../components/StatusMessage";

const DEFAULT_PHRASE = "help me sheguard";
const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const [listening, setListening] = useState(false);
  const [phrase, setPhrase] = useState(localStorage.getItem("sheguard_phrase") || DEFAULT_PHRASE);
  const [heard, setHeard] = useState("");
  const recognitionRef = useRef(null);

  async function startSos(trigger) {
    setError("");
    setStarting(true);
    try {
      const pos = await new Promise((resolve, reject) => {
        if (!navigator.geolocation) return reject(new Error("Geolocation not available on this device"));
        navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 10000 });
      });
      const res = await api.post("/sos/start", {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        trigger,
      });
      navigate(`/emergency/${res.data.session_id}`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Could not start emergency session");
    } finally {
      setStarting(false);
    }
  }

  useEffect(() => {
    localStorage.setItem("sheguard_phrase", phrase);
  }, [phrase]);

  function toggleListening() {
    if (!SpeechRecognitionCtor) {
      setError("Voice recognition (Web Speech API) is not supported in this browser - use the SOS button instead.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setHeard(transcript);
      if (transcript.toLowerCase().includes(phrase.toLowerCase())) {
        recognition.stop();
        startSos("safephrase");
      }
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  useEffect(() => () => recognitionRef.current?.stop(), []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Hi, {user?.name?.split(" ")[0]}</h1>
        <p className="text-sm text-slate-400">You're all set. Tap SOS or say your SafePhrase in an emergency.</p>
      </div>

      <ErrorMessage message={error} />

      <div className="flex flex-col items-center gap-4 py-6">
        <button
          onClick={() => startSos("manual")}
          disabled={starting}
          className="h-40 w-40 rounded-full bg-red-600 hover:bg-red-700 disabled:opacity-60 flex flex-col items-center justify-center gap-2 shadow-lg shadow-red-900/50 active:scale-95 transition"
        >
          <ShieldAlert size={44} />
          <span className="font-bold text-lg">{starting ? "Starting..." : "SOS"}</span>
        </button>
        <p className="text-xs text-slate-500">One tap shares your live location with all guardians</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">SafePhrase voice trigger</div>
            <div className="text-xs text-slate-500">Say this phrase to start an emergency hands-free</div>
          </div>
          <button
            onClick={toggleListening}
            className={`h-11 w-11 rounded-full flex items-center justify-center ${
              listening ? "bg-brand-600 animate-pulse" : "bg-slate-800 border border-slate-700"
            }`}
          >
            {listening ? <Mic size={20} /> : <MicOff size={20} />}
          </button>
        </div>
        <input
          value={phrase}
          onChange={(e) => setPhrase(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          placeholder="Your SafePhrase"
        />
        {listening && (
          <p className="text-xs text-slate-500">
            Listening... {heard && <span className="text-slate-400">heard: "{heard}"</span>}
          </p>
        )}
      </div>
    </div>
  );
}

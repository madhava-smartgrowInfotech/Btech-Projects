import { useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import api from "../api";
import { ErrorMessage } from "../components/StatusMessage";

export default function Assistant() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm your SHEGUARD safety assistant. Ask me anything about staying safe, planning a route, or what to do in an emergency." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef(null);

  async function send() {
    const question = input.trim();
    if (!question) return;
    setError("");
    setInput("");
    setMessages((m) => [...m, { role: "user", text: question }]);
    setSending(true);

    let coords = {};
    try {
      const pos = await new Promise((resolve, reject) =>
        navigator.geolocation
          ? navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 })
          : reject()
      );
      coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
    } catch {
      // location is optional context for the assistant
    }

    try {
      const res = await api.post("/ai/ask", { question, ...coords });
      setMessages((m) => [...m, { role: "assistant", text: res.data.answer }]);
    } catch (err) {
      setError(err.response?.data?.detail || "The assistant is unavailable right now");
    } finally {
      setSending(false);
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles size={20} className="text-brand-400" />
        <h1 className="text-xl font-semibold">AI safety assistant</h1>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
            m.role === "user" ? "ml-auto bg-brand-600" : "bg-slate-900 border border-slate-800"
          }`}>
            {m.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <ErrorMessage message={error} />

      <div className="flex gap-2 mt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask a safety question..."
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
        />
        <button
          onClick={send} disabled={sending}
          className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg px-4 py-2"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}

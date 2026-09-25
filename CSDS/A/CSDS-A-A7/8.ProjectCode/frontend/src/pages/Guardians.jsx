import { useEffect, useState } from "react";
import { UserPlus, Trash2, Send } from "lucide-react";
import api from "../api";
import { Loading, ErrorMessage } from "../components/StatusMessage";

const EMPTY = { name: "", phone: "", email: "", telegram_chat_id: "" };

export default function Guardians() {
  const [guardians, setGuardians] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    api.get("/guardians").then((res) => setGuardians(res.data)).catch(() => setError("Could not load guardians"));
  }

  useEffect(load, []);

  async function addGuardian(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.post("/guardians", form);
      setForm(EMPTY);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add guardian");
    } finally {
      setSaving(false);
    }
  }

  async function removeGuardian(id) {
    try {
      await api.delete(`/guardians/${id}`);
      load();
    } catch {
      setError("Could not remove guardian");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Guardians & settings</h1>
        <p className="text-sm text-slate-400">
          They receive a Telegram message and email with your live tracking link during an emergency.
        </p>
      </div>

      <ErrorMessage message={error} />

      <form onSubmit={addGuardian} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <input
            required placeholder="Name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          />
          <input
            placeholder="Phone" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          />
          <input
            type="email" placeholder="Email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          />
          <input
            placeholder="Telegram chat ID" value={form.telegram_chat_id}
            onChange={(e) => setForm({ ...form, telegram_chat_id: e.target.value })}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm outline-none focus:border-brand-500"
          />
        </div>
        <p className="text-xs text-slate-500">
          Telegram chat ID: have the guardian message your bot and use{" "}
          <code className="text-slate-400">/getUpdates</code> to find their numeric chat_id.
        </p>
        <button
          type="submit" disabled={saving}
          className="flex items-center gap-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg px-4 py-2 text-sm font-medium"
        >
          <UserPlus size={16} /> {saving ? "Adding..." : "Add guardian"}
        </button>
      </form>

      {guardians === null ? (
        <Loading />
      ) : guardians.length === 0 ? (
        <p className="text-sm text-slate-500">No guardians added yet.</p>
      ) : (
        <div className="space-y-2">
          {guardians.map((g) => (
            <div key={g.id} className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg px-4 py-3">
              <div className="flex-1">
                <div className="font-medium">{g.name}</div>
                <div className="text-xs text-slate-500 flex gap-2 flex-wrap">
                  {g.phone && <span>{g.phone}</span>}
                  {g.email && <span>{g.email}</span>}
                  {g.telegram_chat_id && <span className="flex items-center gap-1"><Send size={10} /> Telegram linked</span>}
                </div>
              </div>
              <button onClick={() => removeGuardian(g.id)} className="text-slate-500 hover:text-red-400">
                <Trash2 size={18} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

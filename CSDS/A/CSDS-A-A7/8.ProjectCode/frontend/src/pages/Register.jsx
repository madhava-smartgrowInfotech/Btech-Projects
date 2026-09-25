import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield } from "lucide-react";
import api from "../api";
import { useAuth } from "../AuthContext";
import { ErrorMessage } from "../components/StatusMessage";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/auth/register", { name, email, password });
      login(res.data.access_token, res.data.user);
      navigate("/home");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8 text-brand-400">
          <Shield size={28} />
          <span className="text-2xl font-bold">SHEGUARD</span>
        </div>
        <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h1 className="text-xl font-semibold">Create account</h1>
          <ErrorMessage message={error} />
          <div>
            <label className="text-sm text-slate-400">Name</label>
            <input
              required value={name} onChange={(e) => setName(e.target.value)}
              className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400">Password (min 6 chars)</label>
            <input
              type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 outline-none focus:border-brand-500"
            />
          </div>
          <button
            type="submit" disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 py-2.5 rounded-lg font-medium"
          >
            {loading ? "Creating..." : "Create account"}
          </button>
          <p className="text-sm text-slate-400 text-center">
            Already have an account? <Link to="/login" className="text-brand-400">Log in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}

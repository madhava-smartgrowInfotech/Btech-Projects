import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Leaf, ArrowRight } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import type { Role } from "@/types";

const ROLE_HOME: Record<Role, string> = {
  farmer: "/farmer",
  buyer: "/buyer",
  distributor: "/distributor",
  admin: "/admin",
};

const DEMO_ACCOUNTS = [
  { role: "Farmer", email: "farmer@cropsight.dev" },
  { role: "Buyer", email: "buyer1@cropsight.dev" },
  { role: "Distributor", email: "distributor@cropsight.dev" },
  { role: "Admin", email: "admin@cropsight.dev" },
];

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("cropsight123");
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setAuth(data.access_token, data.user);
      toast.success(`Welcome back, ${data.user.name.split(" ")[0]}`);
      navigate(ROLE_HOME[data.user.role as Role] ?? "/");
    } catch (err) {
      toast.error("Couldn't sign in", apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-sand-50">
      <div className="hidden lg:flex flex-col justify-between bg-brand-950 text-white p-12 relative overflow-hidden">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-brand-600/30 blur-3xl" />
        <div className="absolute -left-24 bottom-0 h-72 w-72 rounded-full bg-lime-500/10 blur-3xl" />
        <Link to="/" className="relative flex items-center gap-2 font-display font-semibold text-lg">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
            <Leaf size={17} />
          </span>
          CropSight
        </Link>
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="relative">
          <p className="font-display text-3xl leading-snug max-w-md">
            "Grading, pricing and delivery — decided in minutes, not market-day guesswork."
          </p>
          <p className="mt-4 text-sm text-brand-200">One platform for farmers, buyers and distributors.</p>
        </motion.div>
        <p className="relative text-xs text-brand-300">© {new Date().getFullYear()} CropSight</p>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="w-full max-w-sm">
          <h1 className="font-display text-2xl font-semibold text-ink-900">Log in</h1>
          <p className="text-sm text-ink-500 mt-1 mb-7">Welcome back to CropSight.</p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Log in"} <ArrowRight size={16} />
            </Button>
          </form>

          <p className="text-sm text-ink-500 mt-6">
            New here?{" "}
            <Link to="/signup" className="text-brand-700 font-medium">
              Create an account
            </Link>
          </p>

          <div className="mt-8 rounded-xl border border-ink-100 bg-white p-4">
            <p className="text-xs font-semibold text-ink-500 mb-2 uppercase tracking-wide">Try a demo account</p>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO_ACCOUNTS.map((d) => (
                <button
                  key={d.email}
                  type="button"
                  onClick={() => {
                    setEmail(d.email);
                    setPassword("cropsight123");
                  }}
                  className="text-left text-xs rounded-lg px-2.5 py-2 hover:bg-ink-50 border border-ink-100"
                >
                  <span className="block font-medium text-ink-800">{d.role}</span>
                  <span className="text-ink-400">{d.email}</span>
                </button>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

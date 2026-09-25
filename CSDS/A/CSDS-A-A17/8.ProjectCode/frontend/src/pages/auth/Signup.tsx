import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Leaf, ArrowRight, Sprout, ShoppingBag, Truck } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { toast } from "@/components/ui/Toast";
import { cn } from "@/lib/format";
import { REGIONS } from "@/lib/staticOptions";
import type { Role } from "@/types";

const ROLE_HOME: Record<Role, string> = {
  farmer: "/farmer",
  buyer: "/buyer",
  distributor: "/distributor",
  admin: "/admin",
};

const ROLE_OPTIONS: { value: "farmer" | "buyer" | "distributor"; label: string; icon: typeof Sprout; blurb: string }[] = [
  { value: "farmer", label: "Farmer", icon: Sprout, blurb: "Grade crops, forecast prices, plan delivery" },
  { value: "buyer", label: "Buyer", icon: ShoppingBag, blurb: "Source graded crops from the marketplace" },
  { value: "distributor", label: "Distributor", icon: Truck, blurb: "Move shipments, monitor cold-chain in transit" },
];

export function Signup() {
  const [role, setRole] = useState<"farmer" | "buyer" | "distributor">("farmer");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [region, setRegion] = useState(REGIONS[0]);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);
  const navigate = useNavigate();

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/signup", { name, email, password, role, region });
      setAuth(data.access_token, data.user);
      toast.success(`Welcome to CropSight, ${name.split(" ")[0]}`);
      navigate(ROLE_HOME[data.user.role as Role] ?? "/");
    } catch (err) {
      toast.error("Couldn't create account", apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-sand-50 p-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-lg bg-white rounded-3xl border border-ink-100 shadow-xl p-8"
      >
        <Link to="/" className="flex items-center gap-2 font-display font-semibold text-lg text-ink-900 mb-6">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Leaf size={17} />
          </span>
          CropSight
        </Link>

        <h1 className="font-display text-2xl font-semibold text-ink-900">Create your account</h1>
        <p className="text-sm text-ink-500 mt-1 mb-6">Join the platform as a farmer, buyer or distributor.</p>

        <div className="grid grid-cols-3 gap-2 mb-6">
          {ROLE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setRole(opt.value)}
              className={cn(
                "rounded-xl border p-3 text-left transition-colors",
                role === opt.value ? "border-brand-500 bg-brand-50" : "border-ink-100 hover:bg-ink-50"
              )}
            >
              <opt.icon size={18} className={role === opt.value ? "text-brand-700" : "text-ink-400"} />
              <p className="text-sm font-semibold text-ink-900 mt-1.5">{opt.label}</p>
              <p className="text-[11px] text-ink-500 mt-0.5 leading-tight">{opt.blurb}</p>
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Full name</Label>
              <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Asha Menon" />
            </div>
            <div>
              <Label htmlFor="region">Region</Label>
              <select
                id="region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full h-10 rounded-xl border border-ink-200 bg-white px-3.5 text-sm text-ink-900 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {REGIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating account…" : "Create account"} <ArrowRight size={16} />
          </Button>
        </form>

        <p className="text-sm text-ink-500 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-700 font-medium">
            Log in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

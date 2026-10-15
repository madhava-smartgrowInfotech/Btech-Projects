import { AlertCircle, ArrowLeft, Building2, ShieldCheck, User } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion/SlideUp";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { homeFor, useAuth } from "@/lib/auth";

const DEMO = [
  { role: "Citizen", icon: <User />, email: "citizen@civicpulse.local", password: "Citizen@123" },
  { role: "Officer", icon: <Building2 />, email: "officer@civicpulse.local", password: "Officer@123" },
  { role: "Admin", icon: <ShieldCheck />, email: "admin@civicpulse.local", password: "Admin@123" },
];

export default function Login() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (user) return <Navigate to={homeFor(user)} replace />;

  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const u = mode === "login" ? await login(form.email, form.password) : await register(form.name, form.email, form.password);
      toast.success(mode === "login" ? `Welcome back, ${u.name.split(" ")[0]}` : "Account created - you can file a complaint now");
      navigate(homeFor(u));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <AuroraBackground />
      <div className="absolute right-4 top-4 flex items-center gap-2">
        <ThemeToggle />
      </div>
      <SlideUp className="w-full max-w-md space-y-4">
        <div className="flex flex-col items-center gap-3">
          <Link to="/" aria-label="CivicPulse home">
            <Logo />
          </Link>
          <Link to="/" className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="size-3.5" /> Back to the home page
          </Link>
        </div>

        <Card strong className="space-y-5 p-6">
          <div className="flex justify-center">
            <Segmented
              label="Account"
              value={mode}
              onChange={(m) => {
                setMode(m);
                setError("");
              }}
              options={[
                { value: "login", label: "Log in" },
                { value: "register", label: "Create citizen account" },
              ]}
            />
          </div>
          <form onSubmit={submit} className="space-y-4" noValidate={false}>
            {mode === "register" && (
              <FormField label="Full name">
                {(p) => <Input {...p} value={form.name} onChange={set("name")} required autoComplete="name" />}
              </FormField>
            )}
            <FormField label="Email">
              {(p) => <Input {...p} type="email" value={form.email} onChange={set("email")} required autoComplete="email" />}
            </FormField>
            <FormField label="Password" hint={mode === "register" ? "At least 8 characters." : undefined}>
              {(p) => (
                <PasswordInput
                  {...p}
                  value={form.password}
                  onChange={set("password")}
                  required
                  minLength={mode === "register" ? 8 : undefined}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
              )}
            </FormField>
            {error && (
              <div role="alert" className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/[0.07] px-3 py-2.5 text-sm text-danger">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            <Button type="submit" className="w-full" size="lg" loading={busy}>
              {mode === "login" ? "Log in" : "Create account"}
            </Button>
          </form>
        </Card>

        {mode === "login" && (
          <Card className="space-y-3 p-4">
            <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Demo accounts</div>
            <div className="grid grid-cols-3 gap-2">
              {DEMO.map((d) => (
                <Button
                  key={d.role}
                  type="button"
                  variant="secondary"
                  size="sm"
                  magnetic={false}
                  aria-label={`Fill in the ${d.role.toLowerCase()} demo account`}
                  onClick={() => {
                    setForm({ ...form, email: d.email, password: d.password });
                    setError("");
                  }}
                >
                  {d.icon} {d.role}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">Tap a role to fill in its credentials, then log in.</p>
          </Card>
        )}
      </SlideUp>
    </div>
  );
}

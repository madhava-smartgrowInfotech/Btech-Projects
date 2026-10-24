import { ArrowRight, KeyRound, Mail, MapPin, Phone, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion/SlideUp";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { LanguageMenu } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { Select } from "@/components/ui/Select";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";

const ROLES = [
  { value: "farmer", label: "Farmer" },
  { value: "officer", label: "Extension officer" },
  { value: "dealer", label: "Agro dealer" },
  { value: "researcher", label: "Researcher" },
];
const MAIN_CROPS = ["tomato", "potato", "corn", "grape", "apple", "pepper", "rice", "wheat"].map((c) => ({ value: c, label: c[0].toUpperCase() + c.slice(1) }));

export default function Register() {
  const { user, register } = useAuth();
  const { lang } = useLang();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", password: "", role: "farmer", region: "", crop: "tomato" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const set = (k: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [k]: v }));

  if (user && !busy) return <Navigate to="/dashboard" replace />;

  const passwordShort = form.password.length > 0 && form.password.length < 6;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register({ ...form, language: lang });
      toast.success("Account created. Welcome to AgriVision!");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <AuroraBackground />
      <div className="absolute right-3 top-3 flex items-center gap-1">
        <LanguageMenu />
        <ThemeToggle />
      </div>
      <SlideUp className="w-full max-w-xl">
        <Link to="/" className="mb-6 flex justify-center" aria-label="AgriVision home">
          <Logo />
        </Link>
        <Card strong className="space-y-5 p-6 sm:p-8">
          <div className="space-y-1">
            <h1 className="font-display text-2xl font-semibold">Join AgriVision</h1>
            <p className="text-sm text-muted-foreground">Free for farmers. Set-up takes about thirty seconds.</p>
          </div>
          <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2" noValidate>
            <FormField label="Full name" className="sm:col-span-2">
              {(p) => <Input {...p} autoComplete="name" value={form.full_name} onChange={(e) => set("full_name")(e.target.value)} placeholder="Ramesh Kumar" icon={<UserRound />} />}
            </FormField>
            <FormField label="Email">
              {(p) => <Input {...p} type="email" required autoComplete="email" value={form.email} onChange={(e) => set("email")(e.target.value)} placeholder="you@example.com" icon={<Mail />} />}
            </FormField>
            <FormField label="Phone">
              {(p) => <Input {...p} type="tel" autoComplete="tel" value={form.phone} onChange={(e) => set("phone")(e.target.value)} placeholder="+919876543210" icon={<Phone />} />}
            </FormField>
            <FormField label="Password" hint="At least 6 characters." error={passwordShort ? "Password must be at least 6 characters." : undefined}>
              {(p) => <PasswordInput {...p} required autoComplete="new-password" value={form.password} onChange={(e) => set("password")(e.target.value)} icon={<KeyRound />} />}
            </FormField>
            <FormField label="Role">
              {(p) => <Select id={p.id} aria-label="Role" value={form.role} onValueChange={set("role")} options={ROLES} />}
            </FormField>
            <FormField label="Region">
              {(p) => <Input {...p} value={form.region} onChange={(e) => set("region")(e.target.value)} placeholder="Maharashtra" icon={<MapPin />} />}
            </FormField>
            <FormField label="Main crop">
              {(p) => <Select id={p.id} aria-label="Main crop" value={form.crop} onValueChange={set("crop")} options={MAIN_CROPS} />}
            </FormField>
            {error && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] px-3 py-2 text-sm text-danger sm:col-span-2">
                {error}
              </p>
            )}
            <Button type="submit" size="lg" className="w-full sm:col-span-2" loading={busy} disabled={!form.email || form.password.length < 6}>
              Create account <ArrowRight />
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground">
            Already registered?{" "}
            <Link to="/login" className="font-medium text-violet-ink hover:underline">
              Sign in
            </Link>
          </p>
        </Card>
      </SlideUp>
    </div>
  );
}

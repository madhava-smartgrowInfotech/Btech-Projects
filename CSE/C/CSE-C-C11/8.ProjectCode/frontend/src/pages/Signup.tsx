import { AtSign, Check, KeyRound, Mail, User, UserPlus, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { AuthShell } from "@/components/auth/AuthShell";
import { Button } from "@/components/ui/Button";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

// Same rules as utils/validators.py so the checklist matches what the server will accept.
const RULES = [
  { label: "8+ characters", test: (p: string) => p.length >= 8 },
  { label: "Uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "Lowercase letter", test: (p: string) => /[a-z]/.test(p) },
  { label: "A digit", test: (p: string) => /[0-9]/.test(p) },
  { label: "Special character", test: (p: string) => /[!@#$%^&*(),.?":{}|<>_\-+=]/.test(p) },
];

export default function Signup() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", username: "", password: "", confirm: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function validate() {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = "Full name is required.";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email.trim())) e.email = "Please enter a valid email address.";
    if (!/^[a-zA-Z0-9_]{3,30}$/.test(form.username)) e.username = "3-30 characters: letters, numbers, underscore only.";
    if (RULES.some((r) => !r.test(form.password))) e.password = "Password does not meet all the rules below.";
    if (form.password !== form.confirm) e.confirm = "Passwords do not match.";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault();
    setFormError(null);
    if (!validate()) return;
    setBusy(true);
    try {
      await api.post("/auth/signup", {
        name: form.name,
        email: form.email,
        username: form.username,
        password: form.password,
        confirm_password: form.confirm,
      });
      await signIn(form.username, form.password);
      toast.success("Account created. Welcome to FINJARVIS!");
      navigate("/app", { replace: true });
    } catch (e) {
      setFormError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Free and local: your data stays on this computer."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-violet-ink hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {formError && (
          <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {formError}
          </p>
        )}
        <FormField label="Full name" error={errors.name}>
          {(p) => <Input {...p} icon={<User />} autoComplete="name" value={form.name} onChange={set("name")} placeholder="Aarav Mehta" autoFocus />}
        </FormField>
        <FormField label="Email" error={errors.email}>
          {(p) => <Input {...p} type="email" icon={<Mail />} autoComplete="email" value={form.email} onChange={set("email")} placeholder="you@example.com" />}
        </FormField>
        <FormField label="Username" error={errors.username}>
          {(p) => <Input {...p} icon={<AtSign />} autoComplete="username" value={form.username} onChange={set("username")} placeholder="aarav_m" />}
        </FormField>
        <FormField label="Password" error={errors.password}>
          {(p) => <PasswordInput {...p} icon={<KeyRound />} autoComplete="new-password" value={form.password} onChange={set("password")} />}
        </FormField>
        <ul className="flex flex-wrap gap-1.5" aria-label="Password rules">
          {RULES.map((r) => {
            const ok = r.test(form.password);
            return (
              <li
                key={r.label}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium",
                  ok ? "border-success/30 bg-success/12 text-success" : "border-[var(--glass-border)] text-muted-foreground",
                )}
              >
                {ok ? <Check className="size-3" aria-label="met" /> : <X className="size-3" aria-label="not met" />}
                {r.label}
              </li>
            );
          })}
        </ul>
        <FormField label="Confirm password" error={errors.confirm}>
          {(p) => <PasswordInput {...p} icon={<KeyRound />} autoComplete="new-password" value={form.confirm} onChange={set("confirm")} />}
        </FormField>
        <Button type="submit" size="lg" className="w-full" loading={busy}>
          <UserPlus /> Create account
        </Button>
      </form>
    </AuthShell>
  );
}

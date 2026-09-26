import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, errorMessage } from "@/lib/api";
import { AuthShell } from "@/pages/auth/AuthShell";

export default function RegisterPage() {
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const mismatch = form.confirm.length > 0 && form.password !== form.confirm;
  const tooShort = form.password.length > 0 && form.password.length < 8;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (mismatch || tooShort) return;
    setBusy(true);
    setError(null);
    try {
      await api.post("/auth/register", { full_name: form.full_name, email: form.email, password: form.password });
      setDone(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <AuthShell title="Request sent" subtitle="An administrator will review your request.">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-xl border bg-success/5 p-6 text-center"
        >
          <CheckCircle2 className="mx-auto size-10 text-success" aria-hidden />
          <p className="mt-3 text-sm">
            Your invigilator account for <strong>{form.email}</strong> is waiting for approval. You can sign in as soon as
            an administrator approves it.
          </p>
          <Button asChild className="mt-5 w-full">
            <Link to="/login">Back to sign in</Link>
          </Button>
        </motion.div>
      </AuthShell>
    );
  }

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <AuthShell
      title="Request an account"
      subtitle="Invigilators request access here. An administrator approves each request."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" autoComplete="name" value={form.full_name} onChange={set("full_name")} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Work email</Label>
          <Input id="email" type="email" autoComplete="email" value={form.email} onChange={set("email")} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={set("password")}
            aria-invalid={tooShort || undefined}
            aria-describedby="password-hint"
            required
          />
          <p id="password-hint" className={tooShort ? "text-xs text-destructive" : "text-xs text-muted-foreground"}>
            At least 8 characters.
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm">Confirm password</Label>
          <Input
            id="confirm"
            type="password"
            autoComplete="new-password"
            value={form.confirm}
            onChange={set("confirm")}
            aria-invalid={mismatch || undefined}
            required
          />
          {mismatch && <p className="text-xs text-destructive">The passwords do not match.</p>}
        </div>
        {error && (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}
        <Button
          type="submit"
          className="w-full"
          size="lg"
          loading={busy}
          disabled={!form.full_name || !form.email || !form.password || mismatch || tooShort}
        >
          Send request
        </Button>
      </form>
    </AuthShell>
  );
}

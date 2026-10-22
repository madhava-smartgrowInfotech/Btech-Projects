import { AtSign, KeyRound, LogIn, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { AuthShell } from "@/components/auth/AuthShell";
import { Button } from "@/components/ui/Button";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export const DEMO = { identifier: "demo", password: "Demo@1234" };

export default function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState<"form" | "demo" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(id: string, pw: string, kind: "form" | "demo") {
    setError(null);
    if (!id.trim() || !pw) {
      setError("Please enter your username or email and your password.");
      return;
    }
    setBusy(kind);
    try {
      await signIn(id.trim(), pw);
      toast.success("Welcome back!");
      navigate((location.state as { from?: string } | null)?.from || "/app", { replace: true });
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void submit(identifier, password, "form");
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to see your money at a glance."
      footer={
        <>
          New to FINJARVIS?{" "}
          <Link to="/signup" className="font-medium text-violet-ink hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {error && (
          <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}
        <FormField label="Username or email">
          {(p) => (
            <Input {...p} icon={<AtSign />} autoComplete="username" value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="you@example.com" autoFocus />
          )}
        </FormField>
        <FormField label="Password">
          {(p) => (
            <PasswordInput {...p} icon={<KeyRound />} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" />
          )}
        </FormField>
        <Button type="submit" size="lg" className="w-full" loading={busy === "form"} disabled={busy !== null}>
          <LogIn /> Log in
        </Button>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="h-px flex-1 bg-[var(--glass-border)]" /> or <span className="h-px flex-1 bg-[var(--glass-border)]" />
        </div>
        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="w-full"
          loading={busy === "demo"}
          disabled={busy !== null}
          onClick={() => void submit(DEMO.identifier, DEMO.password, "demo")}
        >
          <Sparkles /> Try the demo account
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          Demo login: <code className="rounded bg-muted px-1">demo</code> / <code className="rounded bg-muted px-1">Demo@1234</code> — fictional data.
        </p>
      </form>
    </AuthShell>
  );
}

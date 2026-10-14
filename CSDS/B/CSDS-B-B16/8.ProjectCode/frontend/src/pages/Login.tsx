import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { toast } from "sonner";

import { AlertBox } from "@/components/app/AlertBox";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { Logo } from "@/components/brand/Logo";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { SlideUp } from "@/components/motion/SlideUp";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { useAuth } from "@/lib/auth";
import { errorMessage } from "@/lib/api";

const DEMO_ACCOUNTS = [
  { email: "clinician@retinaguard.local", label: "Clinician" },
  { email: "technician@retinaguard.local", label: "Technician" },
];

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const from = (location.state as { from?: string } | null)?.from ?? "/screening/new";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(email.trim(), password);
      toast.success(`Signed in as ${user.name}`);
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <AuroraBackground intensity={0.8} />
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md">
        <SlideUp className="mb-8 flex flex-col items-center gap-3 text-center">
          <Link to="/" aria-label="RetinaGuard home">
            <Logo />
          </Link>
          <p className="text-sm text-muted-foreground">Retinal and cardiovascular screening</p>
        </SlideUp>

        <Card strong sweep={false} className="p-6 sm:p-8">
          <h1 className="font-display text-xl font-semibold">Sign in</h1>
          <p className="mt-1 text-sm text-muted-foreground">Use your account to run and review screenings.</p>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <FormField label="Email" id="login-email">
              {({ id, ...aria }) => (
                <Input id={id} {...aria} type="email" autoComplete="username" required value={email} disabled={busy} onChange={(e) => setEmail(e.target.value)} />
              )}
            </FormField>
            <FormField label="Password" id="login-password">
              {({ id, ...aria }) => (
                <PasswordInput
                  id={id}
                  {...aria}
                  autoComplete="current-password"
                  required
                  value={password}
                  disabled={busy}
                  onChange={(e) => setPassword(e.target.value)}
                />
              )}
            </FormField>

            {error && <AlertBox>{error}</AlertBox>}

            <Button type="submit" size="lg" className="w-full" loading={busy}>
              Sign in
            </Button>
          </form>

          <div className="mt-6 space-y-3 border-t border-[var(--glass-border)] pt-5">
            <p className="text-xs text-muted-foreground">Demo accounts (password in the README)</p>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_ACCOUNTS.map((account) => (
                <Button key={account.email} type="button" variant="outline" size="sm" onClick={() => setEmail(account.email)}>
                  {account.label}
                </Button>
              ))}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

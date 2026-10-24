import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, LogIn, Mail, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { endpoints, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";
  const demo = useQuery({ queryKey: ["demo"], queryFn: endpoints.demo, staleTime: Infinity, retry: 0 });
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={from} replace />;

  async function submit(e?: FormEvent, creds?: { email: string; password: string }) {
    e?.preventDefault();
    const em = creds?.email ?? email;
    const pw = creds?.password ?? password;
    if (!em.trim() || !pw) {
      setError("Enter your email and password, or use the demo account.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await login(em, pw);
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Could not sign in."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <AuroraBackground />
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>
      <SlideUp className="w-full max-w-md">
        <Link to="/" className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-4" /> Back to home
        </Link>
        <Card strong>
          <CardBody className="space-y-6 p-7">
            <div className="space-y-2">
              <Logo />
              <h1 className="font-display text-2xl font-semibold tracking-tight">Sign in</h1>
              <p className="text-sm text-muted-foreground">Open the live monitor, event history and research tools.</p>
            </div>

            <form onSubmit={(e) => void submit(e)} className="space-y-4" noValidate>
              <FormField label="Email">
                {(props) => (
                  <Input {...props} type="email" autoComplete="username" icon={<Mail />} value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
                )}
              </FormField>
              <FormField label="Password">
                {(props) => <PasswordInput {...props} autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />}
              </FormField>
              {error && (
                <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] p-3 text-sm text-danger">
                  {error}
                </p>
              )}
              <Button type="submit" size="lg" className="w-full" loading={busy}>
                <LogIn /> Sign in
              </Button>
            </form>

            <div className="rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-4 text-sm">
              <div className="mb-2 flex items-center gap-2 font-medium">
                <Sparkles className="size-4 text-violet-ink" /> Demo account
              </div>
              {demo.data ? (
                <>
                  <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs text-muted-foreground">
                    <dt>Email</dt>
                    <dd className="select-all font-mono text-foreground">{demo.data.email}</dd>
                    <dt>Password</dt>
                    <dd className="select-all font-mono text-foreground">{demo.data.password}</dd>
                  </dl>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="mt-3 w-full"
                    disabled={busy}
                    onClick={() => {
                      setEmail(demo.data.email);
                      setPassword(demo.data.password);
                      void submit(undefined, demo.data);
                    }}
                  >
                    Use the demo account
                  </Button>
                </>
              ) : demo.isError ? (
                <p className="text-xs text-muted-foreground">The server is not reachable. Start it with run.bat, then reload this page.</p>
              ) : (
                <p className="text-xs text-muted-foreground">Loading demo details…</p>
              )}
            </div>
          </CardBody>
        </Card>
      </SlideUp>
    </div>
  );
}

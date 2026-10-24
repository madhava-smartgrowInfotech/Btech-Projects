import { ArrowRight, KeyRound, Mail, Sprout } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion/SlideUp";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { LanguageMenu } from "@/components/ui/AppShell";

const DEMO = { email: "demo@agrivision.ai", password: "demo1234" };

export default function Login() {
  const { user, login } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user && !busy) return <Navigate to={from} replace />;

  async function submit(e: FormEvent, creds = { email, password }) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const u = await login(creds.email, creds.password);
      toast.success(`Welcome back${u.full_name ? `, ${u.full_name}` : ""}`);
      navigate(from, { replace: true });
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
      <SlideUp className="w-full max-w-md">
        <Link to="/" className="mb-6 flex justify-center" aria-label="AgriVision home">
          <Logo />
        </Link>
        <Card strong className="space-y-5 p-6 sm:p-8">
          <div className="space-y-1">
            <h1 className="font-display text-2xl font-semibold">Welcome back</h1>
            <p className="text-sm text-muted-foreground">Sign in to detect, track and export your crop reports.</p>
          </div>
          <form onSubmit={submit} className="space-y-4" noValidate>
            <FormField label="Email">
              {(p) => (
                <Input {...p} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="farmer@example.com" icon={<Mail />} />
              )}
            </FormField>
            <FormField label="Password">
              {(p) => (
                <PasswordInput {...p} autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" icon={<KeyRound />} />
              )}
            </FormField>
            {error && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] px-3 py-2 text-sm text-danger">
                {error}
              </p>
            )}
            <Button type="submit" size="lg" className="w-full" loading={busy} disabled={!email || !password}>
              {t("common.signin", "Sign in")} <ArrowRight />
            </Button>
          </form>
          <div className="rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-4 text-sm">
            <div className="flex items-center gap-2 font-medium">
              <Sprout className="size-4 text-violet-ink" aria-hidden /> Demo account
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              <b className="text-foreground">{DEMO.email}</b> / <b className="text-foreground">{DEMO.password}</b>
            </p>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="mt-3 w-full"
              disabled={busy}
              onClick={(e) => {
                setEmail(DEMO.email);
                setPassword(DEMO.password);
                void submit(e, DEMO);
              }}
            >
              Sign in as the demo farmer
            </Button>
          </div>
          <p className="text-center text-sm text-muted-foreground">
            New here?{" "}
            <Link to="/register" className="font-medium text-violet-ink hover:underline">
              Create an account
            </Link>
          </p>
        </Card>
      </SlideUp>
    </div>
  );
}

import { AlertCircle, ArrowLeft, LogIn, ShieldCheck, UserRound, Vote, ScanSearch } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion/SlideUp";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { ThemeToggle } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { HOME_BY_ROLE, useAuth } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { label: "Admin", username: "admin", password: "Admin@123", icon: <ShieldCheck />, hint: "Create and run elections" },
  { label: "Voter", username: "voter1", password: "Voter@01pass", icon: <Vote />, hint: "Verify and cast a ballot" },
  { label: "Auditor", username: "auditor", password: "Audit@123", icon: <ScanSearch />, hint: "Verify the ledger" },
];

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const from = (location.state as { from?: string } | null)?.from;

  if (user) return <Navigate to={from && from.startsWith("/app") ? from : HOME_BY_ROLE[user.role]} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const u = await login(username.trim(), password);
      toast.success(`Welcome, ${u.display_name}`);
      navigate(from && from.startsWith("/app") ? from : HOME_BY_ROLE[u.role], { replace: true });
    } catch (err) {
      setError(errorMessage(err, "Could not sign in."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <AuroraBackground />
      <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-4 py-10">
        <div className="mb-6 flex items-center justify-between">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-4" /> Home
          </Link>
          <ThemeToggle />
        </div>
        <SlideUp>
          <Card strong className="space-y-6 p-6 sm:p-8">
            <div className="space-y-3">
              <Logo />
              <div>
                <h1 className="font-display text-2xl font-semibold tracking-tight">Sign in</h1>
                <p className="text-sm text-muted-foreground">Use a demo account to explore the voter, admin or auditor view.</p>
              </div>
              <Badge tone="warning">Demo verification environment · synthetic identities only</Badge>
            </div>

            <form onSubmit={submit} className="space-y-4" noValidate>
              {error && (
                <div role="alert" className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3 py-2.5 text-sm text-danger">
                  <AlertCircle className="mt-0.5 size-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
              <FormField label="Username">
                {(p) => (
                  <Input {...p} name="username" autoComplete="username" required autoFocus value={username} onChange={(e) => setUsername(e.target.value)} icon={<UserRound />} placeholder="admin, voter1 or auditor" />
                )}
              </FormField>
              <FormField label="Password">
                {(p) => <PasswordInput {...p} name="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" />}
              </FormField>
              <Button type="submit" size="lg" className="w-full" loading={busy} disabled={!username || !password}>
                <LogIn /> Sign in
              </Button>
            </form>

            <div className="space-y-2 border-t border-[var(--glass-border)] pt-5">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Quick fill a demo account</p>
              <div className="grid gap-2">
                {DEMO_ACCOUNTS.map((a) => (
                  <button
                    key={a.username}
                    type="button"
                    onClick={() => {
                      setUsername(a.username);
                      setPassword(a.password);
                      setError(null);
                    }}
                    className="glass-flat flex items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-accent"
                  >
                    <span className="grid size-8 place-items-center rounded-lg bg-grad-soft text-violet-ink [&_svg]:size-4">{a.icon}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium">{a.label}</span>
                      <span className="block truncate text-xs text-muted-foreground">
                        {a.username} · {a.hint}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">Voters are voter1 to voter20 (password Voter@01pass to Voter@20pass).</p>
            </div>
          </Card>
        </SlideUp>
      </main>
    </>
  );
}

import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ClipboardCheck, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DemoInfo } from "@/lib/types";
import { AuthShell } from "@/pages/auth/AuthShell";

export default function LoginPage() {
  const { login, token, user } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const demo = useQuery({
    queryKey: ["demo-accounts"],
    queryFn: async () => (await api.get<DemoInfo>("/auth/demo")).data,
    staleTime: Infinity,
    retry: false,
  });

  const next = params.get("next");
  const target = next && next.startsWith("/app") ? next : "/app";
  if (token && user) return <Navigate to={target} replace />;

  async function signIn(emailValue: string, passwordValue: string) {
    setBusy(true);
    setError(null);
    try {
      const signedIn = await login(emailValue, passwordValue);
      toast.success(`Welcome back, ${signedIn.full_name.split(" ")[0]}`);
      navigate(target, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void signIn(email, password);
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle="Exam controllers and invigilators sign in here. Candidates can find their seat without an account."
      footer={
        <>
          New invigilator?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Request an account
          </Link>
          <span className="mx-2">·</span>
          <Link to="/lookup" className="font-medium text-primary hover:underline">
            Find my seat
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            aria-invalid={Boolean(error) || undefined}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            aria-invalid={Boolean(error) || undefined}
          />
        </div>
        {error && (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" size="lg" loading={busy} disabled={!email || !password}>
          Sign in
        </Button>
      </form>

      {demo.data?.enabled && demo.data.password && (
        <div className="mt-8 rounded-xl border bg-muted/40 p-4">
          <div className="text-sm font-medium">Demo workspace</div>
          <p className="mt-1 text-xs text-muted-foreground">Sign in with a sample account to explore SeatWise.</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {demo.data.accounts.map((account) => (
              <Button
                key={account.email}
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => void signIn(account.email, demo.data!.password!)}
              >
                {account.role === "admin" ? <ShieldCheck /> : <ClipboardCheck />}
                {account.role === "admin" ? "Exam controller" : "Invigilator"}
              </Button>
            ))}
          </div>
        </div>
      )}
    </AuthShell>
  );
}

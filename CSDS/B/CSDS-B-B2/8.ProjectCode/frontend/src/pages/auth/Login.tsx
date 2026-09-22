import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { HardHat, ShieldCheck, UserRound } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { nextTarget } from "@/components/common/guards";
import { apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthLayout } from "./AuthLayout";
import { PasswordInput } from "./PasswordInput";

const DEMO_PASSWORD = "Scout@2026";
const DEMOS = [
  { label: "Field user", email: "user@signalscout.demo", icon: UserRound },
  { label: "Engineer", email: "engineer@signalscout.demo", icon: HardHat },
  { label: "Admin", email: "admin@signalscout.demo", icon: ShieldCheck },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const target = nextTarget(`?${params.toString()}`);

  async function submit(e?: FormEvent, creds?: { email: string; password: string }) {
    e?.preventDefault();
    const c = creds ?? { email, password };
    setBusy(true);
    setError(null);
    try {
      const user = await login(c.email.trim(), c.password);
      toast.success(`Welcome, ${user.name}`);
      navigate(target, { replace: true });
    } catch (err) {
      setError(apiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Monitor coverage, track complaints and find better signal."
      footer={
        <>
          New to SignalScout?{" "}
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required aria-invalid={!!error} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <PasswordInput id="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required aria-invalid={!!error} />
        </div>
        {error && (
          <p role="alert" className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}
        <Button type="submit" className="w-full" loading={busy} disabled={!email || !password}>
          Sign in
        </Button>
      </form>

      <div className="mt-6">
        <div className="relative text-center text-xs text-muted-foreground">
          <span className="absolute inset-x-0 top-1/2 h-px bg-border" aria-hidden />
          <span className="relative bg-background px-2">or explore with a demo account</span>
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2">
          {DEMOS.map((d) => (
            <Button
              key={d.email}
              type="button"
              variant="outline"
              className="h-auto flex-col gap-1 py-3 text-xs"
              disabled={busy}
              onClick={() => {
                setEmail(d.email);
                setPassword(DEMO_PASSWORD);
                void submit(undefined, { email: d.email, password: DEMO_PASSWORD });
              }}
            >
              <d.icon className="!size-5 text-primary" />
              {d.label}
            </Button>
          ))}
        </div>
      </div>
    </AuthLayout>
  );
}

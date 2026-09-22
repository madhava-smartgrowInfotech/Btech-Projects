import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Loader2, LogIn, UserRound, Users, BarChart3 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthShell } from "@/pages/auth/AuthShell";
import { apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";

const SAMPLES = [
  { key: "auth.demo.user" as const, id: "demo@upiguardian.app", password: "Guardian@123", icon: UserRound },
  { key: "auth.demo.family" as const, id: "family@upiguardian.app", password: "Guardian@123", icon: Users },
  { key: "auth.demo.admin" as const, id: "admin@upiguardian.app", password: "Admin@1234", icon: BarChart3 },
];

export default function Login() {
  const { t, tx } = useI18n();
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e?: FormEvent, id = identifier, pw = password) => {
    e?.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const user = await login(id.trim(), pw);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from && from !== "/login" ? from : user.role === "admin" ? "/admin" : "/app", { replace: true });
    } catch (err) {
      const d = apiError(err);
      const msg = tx(`error.${d.code}`, d.message);
      setError(msg);
      toast.error(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell>
      <h1 className="font-display text-3xl font-semibold">{t("auth.login.title")}</h1>
      <p className="mt-1 text-muted-foreground">{t("auth.login.subtitle")}</p>

      <form onSubmit={submit} className="mt-8 space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="identifier">{t("auth.identifier")}</Label>
          <Input
            id="identifier"
            autoComplete="username"
            inputMode="email"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">{t("auth.password")}</Label>
          <Input id="password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && (
          <p role="alert" className="rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}
        <Button type="submit" size="lg" className="w-full" disabled={busy || !identifier || !password}>
          {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <LogIn className="mr-2 h-4 w-4" />}
          {t("auth.login.submit")}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        {t("auth.no_account")}{" "}
        <Link to="/register" className="font-medium text-primary hover:underline">
          {t("auth.register.link")}
        </Link>
      </p>

      <div className="mt-8 rounded-2xl border bg-muted/40 p-4">
        <p className="text-sm font-medium">{t("auth.demo.title")}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{t("common.sandbox")}</p>
        <div className="mt-3 space-y-2">
          {SAMPLES.map((s) => (
            <div key={s.id} className="flex items-center gap-3 rounded-xl bg-card px-3 py-2">
              <s.icon className="h-4 w-4 shrink-0 text-primary" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{t(s.key)}</p>
                <p className="truncate font-mono text-2xs text-muted-foreground">{s.id} · {s.password}</p>
              </div>
              <Button
                size="sm"
                variant="secondary"
                disabled={busy}
                onClick={() => {
                  setIdentifier(s.id);
                  setPassword(s.password);
                  void submit(undefined, s.id, s.password);
                }}
              >
                {t("auth.demo.use")}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </AuthShell>
  );
}

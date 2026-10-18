import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, KeyRound, Lock, Mail, Play, User as UserIcon } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";

import { ThemeButton } from "@/components/app/ThemeButton";
import { Logo } from "@/components/brand/Logo";
import { SlideUp } from "@/components/motion";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function Login() {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const demo = useQuery({
    queryKey: ["demo-account"],
    queryFn: async () => (await api.get<{ email: string; password: string }>("/auth/demo")).data,
    retry: false,
    staleTime: Infinity,
  });

  if (user) return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "signin") await login(email.trim(), password);
      else await register(name.trim(), email.trim(), password);
      toast.success(mode === "signin" ? "Signed in." : "Account created. Welcome to AutoSecAI.");
      navigate(from, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function useDemo() {
    if (!demo.data) return;
    setError(null);
    setBusy(true);
    try {
      await login(demo.data.email, demo.data.password);
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
      <div className="absolute left-3 top-3 flex w-[calc(100%-1.5rem)] items-center justify-between">
        <Button asChild variant="ghost" size="sm">
          <Link to="/">
            <ArrowLeft /> Back
          </Link>
        </Button>
        <ThemeButton />
      </div>

      <SlideUp className="w-full max-w-md">
        <Card strong className="space-y-6 p-6 sm:p-8">
          <div className="flex flex-col items-center gap-2 text-center">
            <Logo />
            <h1 className="font-display text-2xl font-semibold">{mode === "signin" ? "Welcome back" : "Create your account"}</h1>
            <p className="text-sm text-muted-foreground">Sign in to review pull requests and ask your codebase questions.</p>
          </div>

          <button
            type="button"
            onClick={useDemo}
            disabled={busy || !demo.data}
            className="flex w-full items-center gap-3 rounded-2xl border border-violet/30 bg-grad-soft p-3 text-left transition-colors hover:border-violet/60 disabled:opacity-60"
          >
            <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-grad-primary text-white">
              <Play className="size-4" />
            </span>
            <span className="min-w-0 text-sm">
              <span className="block font-medium">Use the demo account</span>
              <span className="block truncate text-xs text-muted-foreground">
                {demo.data ? `${demo.data.email} · ${demo.data.password}` : demo.isError ? "Start the API to use the demo account" : "Loading…"}
              </span>
            </span>
          </button>

          <Tabs
            value={mode}
            onValueChange={(v) => {
              setMode(v as typeof mode);
              setError(null);
            }}
            tabs={[
              { value: "signin", label: "Sign in" },
              { value: "signup", label: "Create account" },
            ]}
            className="w-full"
            listClassName="grid w-full grid-cols-2 sm:grid"
          >
            <TabPanel value={mode} className="mt-5">
              <form onSubmit={submit} className="space-y-4" noValidate>
                {mode === "signup" && (
                  <FormField label="Name">
                    {(p) => <Input {...p} icon={<UserIcon />} autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ada Lovelace" required />}
                  </FormField>
                )}
                <FormField label="Email">
                  {(p) => <Input {...p} type="email" icon={<Mail />} autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />}
                </FormField>
                <FormField label="Password" hint={mode === "signup" ? "At least 8 characters." : undefined}>
                  {(p) => (
                    <PasswordInput
                      {...p}
                      icon={mode === "signin" ? <Lock /> : <KeyRound />}
                      autoComplete={mode === "signin" ? "current-password" : "new-password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  )}
                </FormField>
                {error && (
                  <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                    {error}
                  </p>
                )}
                <Button type="submit" className="w-full" loading={busy}>
                  {mode === "signin" ? "Sign in" : "Create account"}
                </Button>
              </form>
            </TabPanel>
          </Tabs>
        </Card>
      </SlideUp>
    </div>
  );
}

import { useMutation } from "@tanstack/react-query";
import { HeartPulse } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router";

import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { api, errorMessage } from "@/lib/api";
import { DEMO_ACCOUNTS } from "@/lib/constants";
import { HOME, type SessionUser, useAuth } from "@/lib/auth";

interface LoginResponse {
  token: string;
  user: SessionUser;
}

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });

  const signIn = useMutation({
    mutationFn: async () => (await api.post<LoginResponse>("/auth/login", form)).data,
    onSuccess: ({ token, user: next }) => {
      login(token, next);
      navigate(HOME[next.role], { replace: true });
    },
  });

  if (user) return <Navigate to={HOME[user.role]} replace />;

  return (
    <>
      <AuroraBackground />
      <main className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center gap-6 px-4 py-10">
        <Link to="/" className="flex items-center justify-center gap-2 font-display text-xl font-bold" aria-label="UniHealth home">
          <HeartPulse className="size-7 text-violet-ink" aria-hidden /> UniHealth
        </Link>

        <Card strong>
          <CardHeader title="Sign in" description="Use a demo account below, or your own." />
          <CardBody>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                signIn.mutate();
              }}
            >
              {signIn.isError && (
                <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] p-3 text-sm text-danger">
                  {errorMessage(signIn.error)}
                </p>
              )}
              <FormField label="Username">
                {(p) => (
                  <Input
                    {...p}
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    autoFocus
                    autoComplete="username"
                    required
                  />
                )}
              </FormField>
              <FormField label="Password">
                {(p) => (
                  <PasswordInput
                    {...p}
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    autoComplete="current-password"
                    required
                  />
                )}
              </FormField>
              <Button type="submit" className="w-full" loading={signIn.isPending}>
                Sign in
              </Button>
            </form>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Demo accounts" description={<>Password for all: <code className="rounded bg-muted px-1">demo123</code></>} />
          <CardBody>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {DEMO_ACCOUNTS.map((d) => (
                <button
                  key={d.username}
                  type="button"
                  onClick={() => setForm({ username: d.username, password: "demo123" })}
                  className="rounded-xl border border-[var(--glass-border)] px-3 py-2 text-left transition-colors hover:border-[color-mix(in_srgb,var(--violet)_50%,transparent)] hover:bg-[var(--glass-hover)]"
                >
                  <div className="text-sm font-medium">{d.label}</div>
                  <div className="text-xs text-muted-foreground">{d.hint}</div>
                </button>
              ))}
            </div>
          </CardBody>
        </Card>
      </main>
    </>
  );
}

import { useState, type FormEvent } from "react";
import { Navigate, Link } from "react-router";
import { toast } from "sonner";

import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/app/ThemeToggle";
import { AuroraBackground } from "@/components/reactbits/AuroraBackground";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/lib/demo";
import { SlideUp } from "@/components/motion/SlideUp";

interface Props {
  mode: "login" | "register";
}

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function AuthPage({ mode }: Props) {
  const { user, login, register } = useAuth();
  const isRegister = mode === "register";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"form" | "demo" | null>(null);

  // Already signed in: go where the user belongs (profile first if it is missing).
  if (user) return <Navigate to={user.has_profile ? "/dashboard" : "/profile"} replace />;

  function validate() {
    const next: typeof errors = {};
    if (isRegister && !name.trim()) next.name = "Enter your name.";
    if (!EMAIL_RE.test(email.trim())) next.email = "Enter a valid email address.";
    if (isRegister ? password.length < 6 : !password) {
      next.password = isRegister ? "Use at least 6 characters." : "Enter your password.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;
    setBusy("form");
    try {
      if (isRegister) {
        await register(name.trim(), email.trim(), password);
        toast.success("Account created. Let's set up your profile.");
      } else {
        const u = await login(email.trim(), password);
        toast.success(`Welcome back, ${u.name}.`);
      }
    } catch (err) {
      setFormError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function trySample() {
    setFormError(null);
    setBusy("demo");
    try {
      const u = await login(DEMO_EMAIL, DEMO_PASSWORD);
      toast.success(`Signed in as the sample account (${u.name}).`);
    } catch (err) {
      setFormError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="relative min-h-dvh">
      <AuroraBackground />
      <header className="px-3 pt-3 sm:px-6">
        <div className="glass mx-auto flex h-14 max-w-6xl items-center gap-2 rounded-2xl px-3">
          <Link to="/" aria-label="NutriSense home" className="mr-auto">
            <Logo />
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main id="main" className="mx-auto grid min-h-[calc(100dvh-5rem)] max-w-md place-items-center px-4 py-10">
        <SlideUp className="w-full">
          <Card strong className="space-y-6 p-6 sm:p-8">
            <div className="space-y-1.5">
              <h1 className="font-display text-2xl font-semibold tracking-tight">{isRegister ? "Create your account" : "Log in"}</h1>
              <p className="text-sm text-muted-foreground">
                {isRegister ? "Save your profile once; plans and logs stay with your account." : "Pick up where you left off."}
              </p>
            </div>

            {formError && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] px-3 py-2 text-sm text-danger">
                {formError}
              </p>
            )}

            <form className="space-y-4" onSubmit={submit} noValidate>
              {isRegister && (
                <FormField label="Your name" error={errors.name}>
                  {(p) => (
                    <Input
                      {...p}
                      autoComplete="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Priya"
                    />
                  )}
                </FormField>
              )}
              <FormField label="Email" error={errors.email}>
                {(p) => (
                  <Input
                    {...p}
                    type="email"
                    autoComplete="email"
                    inputMode="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                  />
                )}
              </FormField>
              <FormField label="Password" hint={isRegister ? "At least 6 characters." : undefined} error={errors.password}>
                {(p) => (
                  <PasswordInput
                    {...p}
                    autoComplete={isRegister ? "new-password" : "current-password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                )}
              </FormField>
              <Button type="submit" className="w-full" size="lg" loading={busy === "form"} disabled={busy !== null}>
                {isRegister ? "Create my account" : "Log in"}
              </Button>
            </form>

            {!isRegister && (
              <div className="space-y-3 border-t border-[var(--glass-border)] pt-5">
                <Button variant="secondary" className="w-full" onClick={trySample} loading={busy === "demo"} disabled={busy !== null}>
                  Try the sample account
                </Button>
                <p className="text-center text-xs text-muted-foreground">Sample data only: {DEMO_EMAIL}</p>
              </div>
            )}

            <p className="text-center text-sm text-muted-foreground">
              {isRegister ? "Already have an account? " : "New here? "}
              <Link to={isRegister ? "/login" : "/register"} className="font-medium text-violet-ink hover:underline">
                {isRegister ? "Log in" : "Create an account"}
              </Link>
            </p>
          </Card>
        </SlideUp>
      </main>
    </div>
  );
}

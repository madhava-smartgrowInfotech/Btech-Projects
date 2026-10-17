import { LogIn, User } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthShell } from "@/pages/AuthShell";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(username.trim(), password);
      toast.success(`Welcome back, ${username.trim()}!`);
      // PublicOnly (App.tsx) moves on to the right screen once the user is set
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to pick up your studies where you left off."
      footer={
        <>
          New here?{" "}
          <Link to="/register" className="font-medium text-violet-ink hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {error && (
          <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.08] px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}
        <FormField label="Username">
          {(p) => (
            <Input {...p} name="username" autoComplete="username" required autoFocus icon={<User />} value={username} onChange={(e) => setUsername(e.target.value)} />
          )}
        </FormField>
        <FormField label="Password">
          {(p) => (
            <PasswordInput {...p} name="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          )}
        </FormField>
        <Button type="submit" size="lg" className="w-full" loading={busy} disabled={!username.trim() || !password}>
          <LogIn /> Sign in
        </Button>
      </form>
    </AuthShell>
  );
}

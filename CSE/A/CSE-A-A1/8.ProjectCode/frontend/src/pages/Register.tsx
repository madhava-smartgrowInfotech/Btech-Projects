import { Target, User, UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { AuthShell } from "@/pages/AuthShell";

export default function Register() {
  const { register, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [interests, setInterests] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(username.trim(), password, interests.trim());
      await login(username.trim(), password);
      toast.success("Account created. Let's add your first notes.");
      // PublicOnly (App.tsx) sends a new user to the Upload screen
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="It takes a few seconds. No email needed."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-violet-ink hover:underline">
            Sign in
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
            <PasswordInput {...p} name="password" autoComplete="new-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          )}
        </FormField>
        <FormField label="Interests / goals (optional)" hint="For example: Data Structures, DBMS, Machine Learning">
          {(p) => <Input {...p} name="interests" icon={<Target />} value={interests} onChange={(e) => setInterests(e.target.value)} />}
        </FormField>
        <Button type="submit" size="lg" className="w-full" loading={busy} disabled={!username.trim() || !password}>
          <UserPlus /> Create account
        </Button>
      </form>
    </AuthShell>
  );
}

import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { toast } from "sonner";

import { FormField, Input, PasswordInput } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";
import { authApi, getErrorMessage } from "@/lib/api.js";
import { FormError } from "@/components/app/FormError.jsx";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      login(res.data.token, res.data.email);
      toast.success("Logged in");
      navigate(location.state?.from ?? "/app", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md pt-6 sm:pt-10">
      <Card className="p-1">
        <CardHeader title="Log in" description="Use the email and password you registered with." />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            <FormField label="Email">
              {(a) => <Input {...a} type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />}
            </FormField>
            <FormField label="Password">
              {(a) => (
                <PasswordInput
                  {...a}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              )}
            </FormField>
            <FormError message={error} />
            <Button type="submit" size="lg" className="w-full" loading={loading} disabled={loading}>
              {loading ? "Logging in…" : "Log in"}
            </Button>
          </form>
          <p className="mt-5 text-center text-sm text-muted-foreground">
            No account yet?{" "}
            <Link to="/register" className="font-medium text-violet-ink hover:underline">
              Sign up
            </Link>
          </p>
        </CardBody>
      </Card>
    </div>
  );
}

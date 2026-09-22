import { useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Bell, KeyRound, UserRound } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/states";
import { ROLE_LABEL } from "@/components/layout/UserMenu";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { api, apiError, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PasswordInput } from "./auth/PasswordInput";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [pw, setPw] = useState({ current: "", next: "" });

  const update = useMutation({
    mutationFn: async (body: Record<string, unknown>) => (await api.patch<User>("/api/auth/me", body)).data,
    onSuccess: (u) => setUser(u),
  });

  if (!user) return null;

  const saveName = (e: FormEvent) => {
    e.preventDefault();
    update.mutate({ name }, { onSuccess: () => toast.success("Name updated"), onError: (err) => toast.error(apiError(err)) });
  };
  const savePassword = (e: FormEvent) => {
    e.preventDefault();
    update.mutate(
      { current_password: pw.current, new_password: pw.next },
      {
        onSuccess: () => {
          toast.success("Password changed");
          setPw({ current: "", next: "" });
        },
        onError: (err) => toast.error(apiError(err)),
      },
    );
  };

  return (
    <>
      <PageHeader title="Profile & notifications" description="Your account details and how SignalScout keeps you informed." />
      <div className="grid max-w-3xl gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserRound className="h-4 w-4 text-primary" /> Account
            </CardTitle>
            <CardDescription className="flex flex-wrap items-center gap-2">
              {user.email} <Badge>{ROLE_LABEL[user.role]}</Badge> {user.is_demo && <Badge variant="secondary">Demo account</Badge>}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={saveName} className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="flex-1 space-y-2">
                <Label htmlFor="name">Display name</Label>
                <Input id="name" value={name} onChange={(e) => setName(e.target.value)} minLength={2} maxLength={120} />
              </div>
              <Button type="submit" disabled={name.trim().length < 2 || name.trim() === user.name} loading={update.isPending && update.variables?.name !== undefined}>
                Save
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-4 w-4 text-primary" /> Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start justify-between gap-4">
              <Label htmlFor="notify" className="flex flex-col gap-1">
                <span>Email me when my complaints change</span>
                <span className="text-xs font-normal text-muted-foreground">Registered, acknowledged, resolved, verified or reopened - sent to {user.email}.</span>
              </Label>
              <Switch
                id="notify"
                checked={user.notify_email}
                onCheckedChange={(v) =>
                  update.mutate({ notify_email: v }, { onSuccess: () => toast.success(v ? "Email updates on" : "Email updates off"), onError: (err) => toast.error(apiError(err)) })
                }
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-primary" /> Password
            </CardTitle>
            {user.is_demo && <CardDescription>Demo account passwords stay fixed so everyone can use them.</CardDescription>}
          </CardHeader>
          <CardContent>
            <form onSubmit={savePassword} className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="current">Current password</Label>
                <PasswordInput id="current" autoComplete="current-password" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} disabled={user.is_demo} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new">New password</Label>
                <PasswordInput id="new" autoComplete="new-password" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} disabled={user.is_demo} />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={user.is_demo || !pw.current || pw.next.length < 8} loading={update.isPending && update.variables?.new_password !== undefined}>
                  Change password
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

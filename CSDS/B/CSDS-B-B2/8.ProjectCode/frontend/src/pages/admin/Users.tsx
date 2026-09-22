import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Users as UsersIcon } from "lucide-react";
import { toast } from "sonner";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { ROLE_LABEL } from "@/components/layout/UserMenu";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { api, apiError, type Role, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime, initials, timeAgo } from "@/lib/utils";

export default function AdminUsers() {
  const qc = useQueryClient();
  const { user: me } = useAuth();
  const [confirm, setConfirm] = useState<User | null>(null);
  const users = useQuery({ queryKey: ["admin-users"], queryFn: async () => (await api.get<User[]>("/api/admin/users")).data });
  const update = useMutation({
    mutationFn: async ({ id, body }: { id: number; body: Partial<Pick<User, "role" | "is_active">> }) => (await api.patch<User>(`/api/admin/users/${id}`, body)).data,
    onSuccess: (u) => {
      qc.setQueryData<User[]>(["admin-users"], (old) => old?.map((x) => (x.id === u.id ? u : x)));
      toast.success(`${u.name} updated`);
    },
    onError: (err) => toast.error(apiError(err)),
  });

  return (
    <>
      <PageHeader title="Users" description="Give network engineers access to the operator desk, or disable accounts that should no longer sign in." />
      {users.isPending ? (
        <Card className="divide-y">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3 p-4">
              <Skeleton className="h-9 w-9 rounded-full" />
              <Skeleton className="h-4 flex-1" />
            </div>
          ))}
        </Card>
      ) : users.isError ? (
        <ErrorState message={apiError(users.error)} onRetry={() => users.refetch()} />
      ) : users.data.length === 0 ? (
        <EmptyState icon={UsersIcon} title="No users yet" />
      ) : (
        <Card className="divide-y overflow-hidden">
          {users.data.map((u) => (
            <div key={u.id} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <Avatar>
                  <AvatarFallback>{initials(u.name)}</AvatarFallback>
                </Avatar>
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-medium">
                    <span className="truncate">{u.name}</span>
                    {u.id === me?.id && <Badge variant="secondary">You</Badge>}
                    {u.is_demo && <Badge variant="outline">Demo</Badge>}
                    {!u.is_active && <Badge variant="destructive">Disabled</Badge>}
                  </p>
                  <p className="truncate text-sm text-muted-foreground">{u.email}</p>
                  <p className="text-xs text-muted-foreground" title={formatDateTime(u.last_login_at)}>
                    Last sign-in {timeAgo(u.last_login_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 sm:justify-end">
                <Select value={u.role} disabled={u.id === me?.id} onValueChange={(v) => update.mutate({ id: u.id, body: { role: v as Role } })}>
                  <SelectTrigger className="w-44" aria-label={`Role of ${u.name}`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(ROLE_LABEL) as Role[]).map((r) => (
                      <SelectItem key={r} value={r}>
                        {ROLE_LABEL[r]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <label className="flex items-center gap-2 text-sm">
                  <Switch
                    checked={u.is_active}
                    disabled={u.id === me?.id}
                    onCheckedChange={(v) => (v ? update.mutate({ id: u.id, body: { is_active: true } }) : setConfirm(u))}
                    aria-label={`${u.is_active ? "Disable" : "Enable"} ${u.name}`}
                  />
                  Active
                </label>
              </div>
            </div>
          ))}
        </Card>
      )}

      <AlertDialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable {confirm?.name}?</AlertDialogTitle>
            <AlertDialogDescription>They will be signed out and cannot sign in until you enable the account again. Their readings and complaints are kept.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              destructive
              onClick={() => {
                if (confirm) update.mutate({ id: confirm.id, body: { is_active: false } });
                setConfirm(null);
              }}
            >
              Disable account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

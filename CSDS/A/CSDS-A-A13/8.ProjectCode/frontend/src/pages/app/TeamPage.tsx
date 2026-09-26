import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, KeyRound, MoreHorizontal, ShieldCheck, UserPlus, UserX, Users } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { initials, timeAgo } from "@/lib/format";
import type { Role, User } from "@/lib/types";

const STATUS_BADGE = {
  active: <Badge variant="success">Active</Badge>,
  pending: <Badge variant="warning">Waiting for approval</Badge>,
  disabled: <Badge variant="secondary">Disabled</Badge>,
} as const;

function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...body }: { id: number } & Partial<Pick<User, "role" | "status" | "full_name">> & { password?: string }) =>
      (await api.patch<User>(`/users/${id}`, body)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
    onError: (err) => toast.error(errorMessage(err)),
  });
}

function AddPersonDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "invigilator" as Role });
  const create = useMutation({
    mutationFn: async () => (await api.post<User>("/users", form)).data,
    onSuccess: (user) => {
      toast.success(`${user.full_name} can now sign in`);
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setForm({ full_name: "", email: "", password: "", role: "invigilator" });
      onOpenChange(false);
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add a person</DialogTitle>
          <DialogDescription>The account is active straight away. Share the password with them securely.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="add-name">Full name</Label>
            <Input id="add-name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-email">Email</Label>
            <Input id="add-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="add-password">Temporary password</Label>
              <Input
                id="add-password"
                type="text"
                autoComplete="off"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={form.role} onValueChange={(role) => setForm({ ...form, role: role as Role })}>
                <SelectTrigger aria-label="Role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="invigilator">Invigilator</SelectItem>
                  <SelectItem value="admin">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          {create.isError && <p className="text-sm text-destructive">{errorMessage(create.error)}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              loading={create.isPending}
              disabled={!form.full_name || !form.email || form.password.length < 8}
            >
              Add person
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ResetPasswordDialog({ user, onClose }: { user: User | null; onClose: () => void }) {
  const [password, setPassword] = useState("");
  const update = useUpdateUser();
  return (
    <Dialog open={Boolean(user)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reset password</DialogTitle>
          <DialogDescription>Set a new password for {user?.full_name}.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="new-password">New password</Label>
          <Input id="new-password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="off" />
          <p className="text-xs text-muted-foreground">At least 8 characters.</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            loading={update.isPending}
            disabled={password.length < 8}
            onClick={() =>
              user &&
              update.mutate(
                { id: user.id, password },
                {
                  onSuccess: () => {
                    toast.success("Password updated");
                    setPassword("");
                    onClose();
                  },
                },
              )
            }
          >
            Save password
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function TeamPage() {
  const { user: me } = useAuth();
  const [adding, setAdding] = useState(false);
  const [resetting, setResetting] = useState<User | null>(null);
  const users = useQuery({ queryKey: ["users"], queryFn: async () => (await api.get<User[]>("/users")).data });
  const update = useUpdateUser();

  const pending = users.data?.filter((u) => u.status === "pending") ?? [];
  const others = users.data?.filter((u) => u.status !== "pending") ?? [];

  return (
    <>
      <PageHeader
        title="Team"
        description="Administrators run imports and plans. Invigilators see their halls and mark attendance."
        actions={
          <Button onClick={() => setAdding(true)}>
            <UserPlus /> Add person
          </Button>
        }
      />

      {users.isPending && <TableSkeleton />}
      {users.isError && <ErrorState error={users.error} onRetry={() => users.refetch()} />}

      {users.data && pending.length > 0 && (
        <Card className="mb-6 border-warning/40">
          <CardHeader>
            <CardTitle>Waiting for approval</CardTitle>
            <CardDescription>These people requested an invigilator account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {pending.map((u) => (
              <div key={u.id} className="flex flex-col gap-3 rounded-lg border p-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="font-medium">{u.full_name}</div>
                  <div className="truncate text-sm text-muted-foreground">
                    {u.email} · requested {timeAgo(u.created_at)}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="success"
                    onClick={() =>
                      update.mutate({ id: u.id, status: "active" }, { onSuccess: () => toast.success(`${u.full_name} approved`) })
                    }
                  >
                    <Check /> Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      update.mutate({ id: u.id, status: "disabled" }, { onSuccess: () => toast.info(`Request from ${u.full_name} declined`) })
                    }
                  >
                    Decline
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {users.data && others.length === 0 && pending.length === 0 && (
        <EmptyState icon={Users} title="No accounts yet" description="Add the people who run your examinations." />
      )}

      {others.length > 0 && (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Person</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden md:table-cell">Last sign-in</TableHead>
                <TableHead className="w-12">
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {others.map((u) => (
                <TableRow key={u.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                        {initials(u.full_name)}
                      </span>
                      <div className="min-w-0">
                        <div className="font-medium">
                          {u.full_name} {u.id === me?.id && <span className="text-xs text-muted-foreground">(you)</span>}
                        </div>
                        <div className="truncate text-xs text-muted-foreground">{u.email}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {u.role === "admin" ? (
                      <Badge>
                        <ShieldCheck /> Administrator
                      </Badge>
                    ) : (
                      <Badge variant="secondary">Invigilator</Badge>
                    )}
                  </TableCell>
                  <TableCell>{STATUS_BADGE[u.status]}</TableCell>
                  <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                    {u.last_login_at ? timeAgo(u.last_login_at) : "Never"}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${u.full_name}`}>
                          <MoreHorizontal />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onSelect={() =>
                            update.mutate(
                              { id: u.id, role: u.role === "admin" ? "invigilator" : "admin" },
                              { onSuccess: () => toast.success("Role updated") },
                            )
                          }
                        >
                          <ShieldCheck /> {u.role === "admin" ? "Make invigilator" : "Make administrator"}
                        </DropdownMenuItem>
                        <DropdownMenuItem onSelect={() => setResetting(u)}>
                          <KeyRound /> Reset password
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className={u.status === "active" ? "text-destructive focus:text-destructive" : undefined}
                          onSelect={() =>
                            update.mutate(
                              { id: u.id, status: u.status === "active" ? "disabled" : "active" },
                              { onSuccess: () => toast.success(u.status === "active" ? "Account disabled" : "Account enabled") },
                            )
                          }
                        >
                          {u.status === "active" ? <UserX /> : <Check />}
                          {u.status === "active" ? "Disable account" : "Enable account"}
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <AddPersonDialog open={adding} onOpenChange={setAdding} />
      <ResetPasswordDialog user={resetting} onClose={() => setResetting(null)} />
    </>
  );
}

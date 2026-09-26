import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, RotateCcw, Save } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/States";
import { RulesFields } from "@/components/rules/RulesFields";
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api, errorMessage } from "@/lib/api";
import type { Rules } from "@/lib/types";

function ResetWorkspace() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState("");
  const reset = useMutation({
    mutationFn: async () => (await api.post("/settings/reset-workspace", { confirm })).data,
    onSuccess: () => {
      toast.success("All exam data was cleared");
      queryClient.invalidateQueries();
      setOpen(false);
      setConfirm("");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  return (
    <Card className="border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="size-4" /> Reset workspace
        </CardTitle>
        <CardDescription>
          Deletes candidates, courses, halls, the timetable, every plan and all attendance. Accounts, settings and the audit
          trail are kept.
        </CardDescription>
      </CardHeader>
      <CardFooter>
        <AlertDialog open={open} onOpenChange={setOpen}>
          <AlertDialogTrigger asChild>
            <Button variant="outline" className="border-destructive/40 text-destructive hover:bg-destructive/10 hover:text-destructive">
              <RotateCcw /> Reset workspace
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete all exam data?</AlertDialogTitle>
              <AlertDialogDescription>This cannot be undone. Type RESET to confirm.</AlertDialogDescription>
            </AlertDialogHeader>
            <Input value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="RESET" aria-label="Type RESET" />
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <Button variant="destructive" disabled={confirm !== "RESET"} loading={reset.isPending} onClick={() => reset.mutate()}>
                Delete everything
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  );
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const rules = useQuery({ queryKey: ["rules"], queryFn: async () => (await api.get<Rules>("/settings/rules")).data });
  const [draft, setDraft] = useState<Rules | null>(null);

  useEffect(() => {
    if (rules.data) setDraft(rules.data);
  }, [rules.data]);

  const save = useMutation({
    mutationFn: async (body: Rules) => (await api.put<Rules>("/settings/rules", body)).data,
    onSuccess: (data) => {
      queryClient.setQueryData(["rules"], data);
      toast.success("Default rules saved");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const dirty = draft && rules.data && JSON.stringify(draft) !== JSON.stringify(rules.data);

  return (
    <>
      <PageHeader title="Settings" description="Workspace defaults. Every plan keeps a copy of the rules it was generated with." />
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Default seating rules</CardTitle>
            <CardDescription>Used to pre-fill new plans. You can still change them for a single plan.</CardDescription>
          </CardHeader>
          <CardContent>
            {rules.isPending && <Skeleton className="h-64 w-full" />}
            {rules.isError && <ErrorState error={rules.error} onRetry={() => rules.refetch()} />}
            {draft && <RulesFields value={draft} onChange={setDraft} showAccessibleDefault />}
          </CardContent>
          {draft && (
            <CardFooter className="justify-end gap-2 border-t pt-5">
              <Button variant="outline" disabled={!dirty} onClick={() => rules.data && setDraft(rules.data)}>
                Undo changes
              </Button>
              <Button disabled={!dirty} loading={save.isPending} onClick={() => draft && save.mutate(draft)}>
                <Save /> Save rules
              </Button>
            </CardFooter>
          )}
        </Card>
        <ResetWorkspace />
      </div>
    </>
  );
}

import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { HeartHandshake, Loader2, Trash2, UserPlus, Users } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { EmptyState, ErrorState, ListSkeleton, PageHeader } from "@/components/common/States";
import { PartyAvatar } from "@/components/risk/RiskBits";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useSettings } from "@/lib/voice";

interface Contact {
  id: number;
  name: string;
  upi_id: string;
  phone_last4: string;
  relation: string | null;
  can_approve: boolean;
}

export default function TrustedContacts() {
  const { t, tx } = useI18n();
  const qc = useQueryClient();
  const settings = useSettings();
  const list = useQuery({ queryKey: ["trusted"], queryFn: async () => (await api.get<{ trusted: Contact[]; protecting: Contact[] }>("/trusted-contacts")).data });
  const [identifier, setIdentifier] = useState("");
  const [relation, setRelation] = useState("");

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["trusted"] });
    qc.invalidateQueries({ queryKey: ["settings"] });
  };
  const add = useMutation({
    mutationFn: async () => (await api.post("/trusted-contacts", { identifier: identifier.trim(), relation: relation || null, can_approve: true })).data,
    onSuccess: () => {
      toast.success(t("trusted.added"));
      setIdentifier("");
      setRelation("");
      refresh();
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/trusted-contacts/${id}`),
    onSuccess: () => {
      toast.success(t("trusted.removed"));
      refresh();
    },
  });
  const toggle = useMutation({
    mutationFn: async (value: boolean) => (await api.put("/settings", { trusted_approval_required: value })).data,
    onSuccess: (d) => qc.setQueryData(["settings"], d),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (identifier.trim().length >= 3) add.mutate();
  };

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <PageHeader title={t("nav.trusted")} subtitle={t("trusted.subtitle")} actions={<GuideButton screen="trusted" />} />

      <div className="surface flex items-start justify-between gap-4 p-5">
        <div>
          <p className="font-medium">{t("trusted.require_approval")}</p>
          <p className="mt-1 text-sm text-muted-foreground">{t("trusted.require_approval_hint")}</p>
          {settings.data && !settings.data.has_trusted_approver && <p className="mt-2 text-xs text-caution">{t("trusted.need_contact_first")}</p>}
        </div>
        <Switch
          checked={!!settings.data?.trusted_approval_required}
          disabled={!settings.data?.has_trusted_approver || toggle.isPending}
          onCheckedChange={(v) => toggle.mutate(v)}
          aria-label={t("trusted.require_approval")}
        />
      </div>

      <section className="surface p-5">
        <h2 className="mb-3 flex items-center gap-2 font-display text-base font-semibold">
          <Users className="h-4 w-4 text-primary" />
          {t("trusted.your_contacts")}
        </h2>
        {list.isLoading ? (
          <ListSkeleton rows={2} />
        ) : list.isError ? (
          <ErrorState error={list.error} onRetry={() => list.refetch()} />
        ) : list.data?.trusted.length ? (
          <ul className="divide-y">
            {list.data.trusted.map((c) => (
              <li key={c.id} className="flex items-center gap-3 py-3">
                <PartyAvatar party={{ name: c.name, is_merchant: false }} />
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {c.upi_id} · ••{c.phone_last4}
                    {c.relation ? ` · ${c.relation}` : ""}
                  </p>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="ghost" size="icon" aria-label={t("trusted.remove")}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>{t("trusted.remove_title", { name: c.name })}</AlertDialogTitle>
                      <AlertDialogDescription>{t("trusted.remove_body")}</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                      <AlertDialogAction onClick={() => remove.mutate(c.id)}>{t("trusted.remove")}</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState icon={HeartHandshake} title={t("trusted.empty")} description={t("trusted.empty_hint")} className="py-8" />
        )}

        <form onSubmit={submit} className="mt-4 grid gap-3 border-t pt-4 sm:grid-cols-[1fr_10rem_auto] sm:items-end">
          <div className="space-y-2">
            <Label htmlFor="tc-id">{t("trusted.identifier")}</Label>
            <Input id="tc-id" value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="arjun@upg / 9000000002" autoCapitalize="none" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tc-rel">{t("trusted.relation")}</Label>
            <Input id="tc-rel" value={relation} onChange={(e) => setRelation(e.target.value)} placeholder={t("trusted.relation_placeholder")} />
          </div>
          <Button type="submit" disabled={identifier.trim().length < 3 || add.isPending}>
            {add.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UserPlus className="mr-2 h-4 w-4" />}
            {t("trusted.add")}
          </Button>
        </form>
      </section>

      <section className="surface p-5">
        <h2 className="mb-1 font-display text-base font-semibold">{t("trusted.protecting")}</h2>
        <p className="mb-3 text-sm text-muted-foreground">{t("trusted.protecting_hint")}</p>
        {list.data?.protecting.length ? (
          <ul className="divide-y">
            {list.data.protecting.map((c) => (
              <li key={c.id} className="flex items-center gap-3 py-3">
                <PartyAvatar party={{ name: c.name, is_merchant: false }} />
                <div className="flex-1">
                  <p className="font-medium">{c.name}</p>
                  <p className="text-xs text-muted-foreground">{c.upi_id}</p>
                </div>
                <Button asChild variant="outline" size="sm">
                  <Link to="/app/approvals">{t("nav.approvals")}</Link>
                </Button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">{t("trusted.protecting_none")}</p>
        )}
      </section>
    </div>
  );
}

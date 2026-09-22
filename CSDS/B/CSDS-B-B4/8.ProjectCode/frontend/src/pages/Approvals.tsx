import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Check, Clock3, ShieldCheck, X } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, ListSkeleton, PageHeader } from "@/components/common/States";
import { LevelBadge, PartyRow, ReasonList } from "@/components/risk/RiskBits";
import { api, apiError } from "@/lib/api";
import { formatCountdown, formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Assessment, Party } from "@/lib/types";
import { useNow } from "@/lib/useNow";

interface Approval {
  hold_id: number;
  status: string;
  approval_status: string;
  hold_until: string;
  decided_at: string | null;
  created_at: string;
  amount: number;
  note: string | null;
  channel: string;
  requested_by: { name: string; upi_id: string };
  payee: Party;
  assessment: Assessment | null;
  intent: { purpose: string; matched_scam_type: string | null } | null;
}

export default function Approvals() {
  const { t, tx, lang } = useI18n();
  const qc = useQueryClient();
  const now = useNow(1000);
  const list = useQuery({ queryKey: ["approvals"], queryFn: async () => (await api.get<{ items: Approval[] }>("/approvals")).data, refetchInterval: 15000 });
  const decide = useMutation({
    mutationFn: async ({ id, approve }: { id: number; approve: boolean }) => (await api.post(`/approvals/${id}/${approve ? "approve" : "reject"}`)).data,
    onSuccess: (_, v) => {
      toast.success(v.approve ? t("approvals.approved") : t("approvals.rejected"));
      qc.invalidateQueries({ queryKey: ["approvals"] });
      qc.invalidateQueries({ queryKey: ["badges"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const pending = list.data?.items.filter((a) => a.status === "active" && a.approval_status === "pending") ?? [];
  const done = list.data?.items.filter((a) => !(a.status === "active" && a.approval_status === "pending")) ?? [];

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <PageHeader title={t("nav.approvals")} subtitle={t("approvals.subtitle")} />
      {list.isLoading ? (
        <ListSkeleton rows={2} />
      ) : list.isError ? (
        <ErrorState error={list.error} onRetry={() => list.refetch()} />
      ) : pending.length === 0 && done.length === 0 ? (
        <EmptyState icon={ShieldCheck} title={t("approvals.empty")} description={t("approvals.empty_hint")} />
      ) : (
        <>
          {pending.map((a) => (
            <motion.div key={a.hold_id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="surface overflow-hidden border-caution/50">
              <div className="flex items-center justify-between bg-caution-soft px-4 py-2.5 text-sm font-medium text-caution">
                <span className="flex items-center gap-2">
                  <Clock3 className="h-4 w-4" />
                  {t("approvals.waiting", { name: a.requested_by.name })}
                </span>
                <span className="tabular">{formatCountdown(new Date(a.hold_until).getTime() - now)}</span>
              </div>
              <div className="space-y-4 p-4">
                <PartyRow party={a.payee} sub={t("approvals.to")} right={<span className="font-display text-xl font-semibold tabular">{formatINR(a.amount)}</span>} />
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  {a.assessment && <LevelBadge level={a.assessment.final_level} />}
                  {a.assessment && <span className="text-muted-foreground">{t("risk.score")} {a.assessment.score}</span>}
                  {a.intent && <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{t("approvals.purpose", { purpose: tx(`purpose.${a.intent.purpose}`, a.intent.purpose) })}</span>}
                </div>
                {a.assessment && <ReasonList reasons={a.assessment.reasons} />}
                <p className="text-sm text-muted-foreground">{t("approvals.call_first", { name: a.requested_by.name })}</p>
                <div className="flex gap-2">
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="default" className="flex-1 bg-danger text-danger-foreground hover:bg-danger/90">
                        <X className="mr-1.5 h-4 w-4" />
                        {t("approvals.reject")}
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>{t("approvals.reject_title")}</AlertDialogTitle>
                        <AlertDialogDescription>{t("approvals.reject_body", { amount: formatINR(a.amount), name: a.requested_by.name })}</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                        <AlertDialogAction onClick={() => decide.mutate({ id: a.hold_id, approve: false })}>{t("approvals.reject")}</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" className="flex-1">
                        <Check className="mr-1.5 h-4 w-4" />
                        {t("approvals.approve")}
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>{t("approvals.approve_title")}</AlertDialogTitle>
                        <AlertDialogDescription>{t("approvals.approve_body", { amount: formatINR(a.amount), payee: a.payee.name })}</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                        <AlertDialogAction onClick={() => decide.mutate({ id: a.hold_id, approve: true })}>{t("approvals.approve")}</AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>
            </motion.div>
          ))}
          {done.length > 0 && (
            <section>
              <h2 className="mb-2 text-sm font-medium text-muted-foreground">{t("approvals.history")}</h2>
              <ul className="surface divide-y">
                {done.map((a) => (
                  <li key={a.hold_id} className="p-4">
                    <PartyRow
                      party={a.payee}
                      sub={`${a.requested_by.name} · ${formatDateTime(a.created_at, lang)} · ${tx(`approval.${a.approval_status}`, a.approval_status)} / ${tx(`hold.status.${a.status}`, a.status)}`}
                      right={<span className="font-semibold tabular">{formatINR(a.amount)}</span>}
                    />
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

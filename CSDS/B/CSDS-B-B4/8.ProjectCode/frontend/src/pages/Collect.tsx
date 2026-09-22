import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ArrowDownLeft, Bell, Loader2, Send, ShieldAlert, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorState, ListSkeleton, PageHeader } from "@/components/common/States";
import { HighlightedText } from "@/components/risk/HighlightedText";
import { PartyRow, TrustBadge } from "@/components/risk/RiskBits";
import { GuideButton, SpeakButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { CollectItem, Payment } from "@/lib/types";
import { cn } from "@/lib/utils";

function IncomingCard({ item }: { item: CollectItem }) {
  const { t, tx, lang } = useI18n();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const pending = item.status === "pending";
  const deceptive = item.guard?.flags?.includes("deceptive_note");
  const review = useMutation({
    mutationFn: async () => (await api.post<Payment>(`/collect/${item.id}/assess`)).data,
    onSuccess: (p) => navigate(`/app/pay/${p.id}`),
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const decline = useMutation({
    mutationFn: async () => (await api.post(`/collect/${item.id}/decline`)).data,
    onSuccess: () => {
      toast.success(t("collect.declined"));
      qc.invalidateQueries({ queryKey: ["collect"] });
      qc.invalidateQueries({ queryKey: ["badges"] });
    },
  });
  return (
    <motion.li layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={cn("surface overflow-hidden", pending && deceptive && "border-danger/50")}>
      {pending && (
        <div className={cn("flex items-center gap-2 px-4 py-2.5 text-sm font-semibold", deceptive ? "bg-danger text-danger-foreground" : "bg-caution-soft text-caution")}>
          <ShieldAlert className="h-4 w-4 shrink-0" />
          {t("collect.debit_banner", { amount: formatINR(item.amount) })}
        </div>
      )}
      <div className="space-y-3 p-4">
        <PartyRow
          party={item.counterparty}
          sub={formatDateTime(item.created_at, lang)}
          right={<span className="font-display text-xl font-semibold tabular">{formatINR(item.amount)}</span>}
        />
        {item.note && (
          <div className="rounded-xl bg-muted/60 p-3 text-sm">
            <p className="mb-1 text-2xs font-semibold uppercase tracking-wide text-muted-foreground">{t("collect.their_note")}</p>
            <HighlightedText text={item.note} highlights={item.guard?.note?.highlights ?? []} />
          </div>
        )}
        {pending && deceptive && <p className="text-sm font-medium text-danger">{t("collect.deceptive_explain")}</p>}
        <div className="flex flex-wrap items-center gap-2">
          {item.guard?.requester_trust && <TrustBadge trust={item.guard.requester_trust} />}
          {!pending && <span className="rounded-full bg-muted px-2 py-1 text-xs">{tx(`collect.status.${item.status}`, item.status)}</span>}
        </div>
        {pending && (
          <div className="flex flex-col gap-2 pt-1 sm:flex-row sm:items-center">
            <SpeakButton source={{ kind: "collect", id: item.id }} autoPlay={deceptive} />
            <div className="flex flex-1 gap-2 sm:justify-end">
              <Button variant="outline" className="flex-1 sm:flex-none" onClick={() => decline.mutate()} disabled={decline.isPending}>
                <X className="mr-1.5 h-4 w-4" />
                {t("collect.decline")}
              </Button>
              <Button className="flex-1 sm:flex-none" onClick={() => review.mutate()} disabled={review.isPending}>
                {review.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {t("collect.review_pay")}
              </Button>
            </div>
          </div>
        )}
      </div>
    </motion.li>
  );
}

function RequestForm() {
  const { t, tx } = useI18n();
  const qc = useQueryClient();
  const [upi, setUpi] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const create = useMutation({
    mutationFn: async () => (await api.post("/collect", { upi_id: upi.trim().toLowerCase(), amount: Number(amount), note: note || null })).data,
    onSuccess: () => {
      toast.success(t("collect.sent"));
      setUpi("");
      setAmount("");
      setNote("");
      qc.invalidateQueries({ queryKey: ["collect"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const submit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };
  return (
    <form onSubmit={submit} className="surface space-y-4 p-5">
      <p className="text-sm text-muted-foreground">{t("collect.request_hint")}</p>
      <div className="space-y-2">
        <Label htmlFor="c-upi">{t("collect.from_upi")}</Label>
        <Input id="c-upi" value={upi} onChange={(e) => setUpi(e.target.value)} placeholder="name@upg" autoCapitalize="none" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="c-amt">{t("send.amount")}</Label>
          <Input id="c-amt" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ""))} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="c-note">{t("send.note")}</Label>
          <Input id="c-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={140} placeholder={t("collect.note_placeholder")} />
        </div>
      </div>
      <Button type="submit" disabled={!upi || !(Number(amount) > 0) || create.isPending}>
        {create.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
        {t("collect.send_request")}
      </Button>
    </form>
  );
}

export default function Collect() {
  const { t, tx, lang } = useI18n();
  const incoming = useQuery({ queryKey: ["collect", "incoming"], queryFn: async () => (await api.get<{ items: CollectItem[] }>("/collect/incoming")).data });
  const outgoing = useQuery({ queryKey: ["collect", "outgoing"], queryFn: async () => (await api.get<{ items: CollectItem[] }>("/collect/outgoing")).data });
  const pending = incoming.data?.items.filter((i) => i.status === "pending") ?? [];
  const past = incoming.data?.items.filter((i) => i.status !== "pending") ?? [];

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title={t("nav.collect")} subtitle={t("collect.subtitle")} actions={<GuideButton screen="collect" />} />
      <div className="mb-4 flex items-start gap-3 rounded-2xl border border-primary/30 bg-primary/5 p-4 text-sm">
        <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        <p>{t("collect.rule")}</p>
      </div>
      <Tabs defaultValue="incoming">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="incoming">
            {t("collect.tab.incoming")} {pending.length > 0 && <span className="ml-1.5 rounded-full bg-danger px-1.5 text-[10px] text-danger-foreground">{pending.length}</span>}
          </TabsTrigger>
          <TabsTrigger value="outgoing">{t("collect.tab.outgoing")}</TabsTrigger>
          <TabsTrigger value="new">{t("collect.tab.new")}</TabsTrigger>
        </TabsList>
        <TabsContent value="incoming" className="space-y-4">
          {incoming.isLoading ? (
            <ListSkeleton rows={3} />
          ) : incoming.isError ? (
            <ErrorState error={incoming.error} onRetry={() => incoming.refetch()} />
          ) : incoming.data?.items.length ? (
            <>
              <ul className="space-y-3">
                {pending.map((i) => (
                  <IncomingCard key={i.id} item={i} />
                ))}
              </ul>
              {past.length > 0 && (
                <>
                  <p className="pt-2 text-sm font-medium text-muted-foreground">{t("collect.earlier")}</p>
                  <ul className="space-y-3 opacity-80">
                    {past.slice(0, 10).map((i) => (
                      <IncomingCard key={i.id} item={i} />
                    ))}
                  </ul>
                </>
              )}
            </>
          ) : (
            <EmptyState icon={Bell} title={t("collect.empty")} description={t("collect.empty_hint")} />
          )}
        </TabsContent>
        <TabsContent value="outgoing">
          {outgoing.isLoading ? (
            <ListSkeleton rows={2} />
          ) : outgoing.data?.items.length ? (
            <ul className="surface divide-y">
              {outgoing.data.items.map((i) => (
                <li key={i.id} className="p-4">
                  <PartyRow party={i.counterparty} sub={`${formatDateTime(i.created_at, lang)} · ${tx(`collect.status.${i.status}`, i.status)}`} right={<span className="font-semibold tabular">{formatINR(i.amount)}</span>} />
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState icon={ArrowDownLeft} title={t("collect.none_sent")} />
          )}
        </TabsContent>
        <TabsContent value="new">
          <RequestForm />
        </TabsContent>
      </Tabs>
    </div>
  );
}

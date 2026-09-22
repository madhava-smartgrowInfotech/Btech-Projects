import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { AtSign, IndianRupee, Loader2, ShieldCheck, UserSearch } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/common/States";
import { PartyAvatar, PartyRow, TrustBadge } from "@/components/risk/RiskBits";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { PayeeLookup, Payment, SavedPayee } from "@/lib/types";
import { cn } from "@/lib/utils";

function useDebounced<T>(value: T, ms = 400) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = window.setTimeout(() => setV(value), ms);
    return () => window.clearTimeout(id);
  }, [value, ms]);
  return v;
}

export function deviceType(): "mobile" | "desktop" | "tablet" {
  const ua = navigator.userAgent.toLowerCase();
  if (/ipad|tablet/.test(ua)) return "tablet";
  if (/mobi|android|iphone/.test(ua)) return "mobile";
  return "desktop";
}

export async function currentPosition(): Promise<{ lat: number; lon: number } | null> {
  if (!("geolocation" in navigator) || !window.isSecureContext) return null;
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => resolve(null),
      { timeout: 2500, maximumAge: 600_000 },
    );
  });
}

export default function Send() {
  const { t, tx } = useI18n();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [upi, setUpi] = useState(params.get("to") ?? "");
  const [amount, setAmount] = useState(params.get("amount") ?? "");
  const [note, setNote] = useState("");
  const debounced = useDebounced(upi.trim().toLowerCase());
  const validUpi = /^[a-z0-9._-]{2,64}@[a-z]{2,32}$/.test(debounced);

  const recent = useQuery({ queryKey: ["payees"], queryFn: async () => (await api.get<{ saved: SavedPayee[]; recent: SavedPayee[] }>("/payees/recent")).data });
  const lookup = useQuery({
    queryKey: ["payee", debounced],
    queryFn: async () => (await api.get<PayeeLookup>("/payees/lookup", { params: { upi_id: debounced } })).data,
    enabled: validUpi,
    retry: false,
  });

  const assess = useMutation({
    mutationFn: async () => {
      const geo = await currentPosition();
      return (
        await api.post<Payment>("/payments/assess", {
          upi_id: debounced,
          amount: Number(amount),
          note: note || null,
          device: deviceType(),
          ...(geo ? { lat: geo.lat, lon: geo.lon } : {}),
        })
      ).data;
    },
    onSuccess: (p) => navigate(`/app/pay/${p.id}`),
    onError: (err) => {
      const d = apiError(err);
      toast.error(tx(`error.${d.code}`, d.message));
    },
  });

  const amountNum = Number(amount);
  const amountOk = amountNum > 0 && amountNum <= 100000;
  const canSubmit = validUpi && lookup.data && !lookup.data.is_self && amountOk && !assess.isPending;
  const chips = useMemo(() => [...(recent.data?.saved ?? []), ...(recent.data?.recent ?? [])].slice(0, 10), [recent.data]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (canSubmit) assess.mutate();
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title={t("nav.send")} subtitle={t("send.subtitle")} actions={<GuideButton screen="send" />} />

      <section className="mb-5">
        <p className="mb-2 text-sm font-medium">{t("send.saved")}</p>
        <div className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0">
          {recent.isLoading &&
            [0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-20 shrink-0 rounded-2xl" />
            ))}
          {chips.map((c) => (
            <motion.button
              key={c.upi_id}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => setUpi(c.upi_id)}
              className={cn(
                "flex w-20 shrink-0 flex-col items-center gap-1.5 rounded-2xl border bg-card p-2 text-center text-xs transition hover:border-primary/50",
                debounced === c.upi_id && "border-primary ring-2 ring-primary/20",
              )}
            >
              <PartyAvatar party={c} size="sm" />
              <span className="line-clamp-2 leading-tight">{c.nickname ?? c.name}</span>
            </motion.button>
          ))}
        </div>
      </section>

      <form onSubmit={submit} className="surface space-y-5 p-5">
        <div className="space-y-2">
          <Label htmlFor="upi">{t("send.upi_id")}</Label>
          <div className="relative">
            <AtSign className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="upi" value={upi} onChange={(e) => setUpi(e.target.value)} placeholder="name@upg" className="pl-9" autoComplete="off" autoCapitalize="none" spellCheck={false} />
          </div>
          <div className="min-h-[3.5rem]">
            {validUpi && lookup.isLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> {t("send.looking_up")}
              </div>
            )}
            {validUpi && lookup.isError && (
              <p className="flex items-center gap-2 text-sm text-danger">
                <UserSearch className="h-4 w-4" />
                {tx(`error.${apiError(lookup.error).code}`, apiError(lookup.error).message)}
              </p>
            )}
            {lookup.data && validUpi && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="rounded-xl border bg-muted/40 p-3">
                <PartyRow
                  party={lookup.data}
                  sub={lookup.data.times_paid ? t("send.paid_before", { n: lookup.data.times_paid }) : t("send.never_paid")}
                  right={<TrustBadge trust={lookup.data.trust} />}
                />
                {lookup.data.is_self && <p className="mt-2 text-xs text-danger">{t("error.self_payment")}</p>}
              </motion.div>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="amount">{t("send.amount")}</Label>
          <div className="relative">
            <IndianRupee className="pointer-events-none absolute left-3 top-1/2 h-6 w-6 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="amount"
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value.replace(/[^\d.]/g, ""))}
              placeholder="0"
              className="h-16 pl-11 font-display text-3xl font-semibold tabular"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {[100, 500, 1000, 2000, 5000].map((v) => (
              <Button key={v} type="button" variant="secondary" size="sm" onClick={() => setAmount(String(v))}>
                {formatINR(v)}
              </Button>
            ))}
          </div>
          {amount && !amountOk && <p className="text-xs text-danger">{t("error.amount_invalid")}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="note">
            {t("send.note")} <span className="text-muted-foreground">({t("common.optional")})</span>
          </Label>
          <Input id="note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={140} placeholder={t("send.note_placeholder")} />
        </div>

        <Button type="submit" size="lg" className="w-full" disabled={!canSubmit}>
          {assess.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
          {t("send.check_and_pay")}
        </Button>
        <p className="text-center text-xs text-muted-foreground">{t("send.check_hint")}</p>
      </form>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { ArrowLeft, Ban, ChevronDown, Info, QrCode, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ErrorState, FullScreenLoader } from "@/components/common/States";
import { ContributionBars, LevelBadge, PartyRow, ReasonList, RiskGauge, TrustBadge, pick } from "@/components/risk/RiskBits";
import { SpeakButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { IntentResult, Payment } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSettings } from "@/lib/voice";
import { HoldView } from "@/pages/pay/HoldView";
import { IntentStep } from "@/pages/pay/IntentStep";
import { PinPad } from "@/pages/pay/PinPad";
import { CancelledView, SuccessView } from "@/pages/pay/Outcome";
import { ReportButton } from "@/pages/pay/shared";

type Step = "review" | "intent" | "warning" | "pin";

export default function PaymentFlow() {
  const { id } = useParams();
  const { t, tx, lang } = useI18n();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("review");
  const [intentResult, setIntentResult] = useState<IntentResult | null>(null);
  const [whyOpen, setWhyOpen] = useState(false);
  const [understood, setUnderstood] = useState(false);
  const settings = useSettings();

  const q = useQuery({
    queryKey: ["payment", Number(id)],
    queryFn: async () => (await api.get<Payment>(`/payments/${id}`)).data,
    refetchInterval: (query) => (query.state.data?.status === "held" ? 5000 : false),
  });
  const p = q.data;

  const setPayment = (next: Payment) => {
    qc.setQueryData(["payment", Number(id)], next);
    for (const k of ["wallet", "payments", "holds", "badges", "collect", "me"]) qc.invalidateQueries({ queryKey: [k] });
  };

  const cancel = useMutation({
    mutationFn: async () => (await api.post<Payment>(`/payments/${id}/cancel`)).data,
    onSuccess: (next) => {
      setPayment(next);
      toast.success(t("pay.cancelled_toast"));
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  useEffect(() => {
    if (p?.intent && step === "review" && p.status === "draft") {
      // Returning to a payment that already has an intent answer.
      setStep("warning");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p?.id]);

  if (q.isLoading) return <FullScreenLoader />;
  if (q.isError || !p) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;

  const a = p.assessment;
  if (p.status === "held") return <HoldView payment={p} onCancel={() => cancel.mutate()} cancelling={cancel.isPending} />;
  if (p.status === "completed") return <SuccessView payment={p} />;
  if (["cancelled", "rejected", "blocked", "declined"].includes(p.status)) return <CancelledView payment={p} />;
  if (!a) return <ErrorState error={new Error(t("pay.no_assessment"))} />;

  const blocked = a.action === "block";
  const level = intentResult?.final_level ?? a.final_level;
  const needsIntent = a.level !== "low";
  const guard = a.guard ?? {};
  const holdMinutes = settings.data?.hold_minutes ?? 30;
  const warning = intentResult?.warning ?? p.intent?.warning ?? null;
  const recommendCancel = intentResult?.recommend_cancel ?? !!p.intent?.matched_scam_type;

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <Button variant="ghost" size="sm" onClick={() => (step === "review" ? navigate(-1) : setStep(step === "pin" && needsIntent ? "warning" : step === "warning" ? "intent" : "review"))}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          {t("common.back")}
        </Button>
        <Steps step={step} needsIntent={needsIntent && !blocked} />
      </div>

      {/* Payee + amount header */}
      <div className="surface mb-4 flex items-center justify-between gap-3 p-4">
        <PartyRow party={p.counterparty} sub={<span className="flex items-center gap-1.5">{p.channel === "qr" && <QrCode className="h-3 w-3" />}{p.counterparty.upi_id}</span>} className="min-w-0 flex-1" />
        <div className="text-right">
          <p className="font-display text-2xl font-semibold tabular">{formatINR(p.amount)}</p>
          {p.note && <p className="max-w-[10rem] truncate text-xs text-muted-foreground">{p.note}</p>}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === "review" && (
          <motion.div key="review" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="space-y-4">
            {/* Guard banners (F9) */}
            {guard.type === "collect" && (
              <div className="rounded-2xl border-2 border-danger bg-danger-soft p-4">
                <p className="flex items-center gap-2 font-display text-lg font-semibold text-danger">
                  <ShieldAlert className="h-5 w-5" />
                  {t("collect.debit_banner", { amount: formatINR(p.amount) })}
                </p>
                <p className="mt-1 text-sm">{t("collect.never_to_receive")}</p>
              </div>
            )}
            {guard.type === "qr" && (guard.flags?.length ?? 0) > 0 && (
              <div className="rounded-2xl border-2 border-danger bg-danger-soft p-4">
                <p className="flex items-center gap-2 font-semibold text-danger">
                  <QrCode className="h-5 w-5" />
                  {t("qr.guard_title")}
                </p>
                <ul className="mt-1 list-inside list-disc text-sm">
                  {guard.flags!.map((f) => (
                    <li key={f}>{tx(`qr.flag.${f}`, f, { name: guard.payee_name_in_qr ?? "", registered: guard.registered_name ?? "" })}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="surface p-5">
              <div className="grid items-center gap-5 sm:grid-cols-[220px_1fr]">
                <RiskGauge score={a.score} level={blocked ? "high" : a.level} />
                <div className="min-w-0">
                  <p className="font-display text-xl font-semibold">{blocked ? t("pay.headline.block") : tx(`pay.headline.${a.level}`)}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{blocked ? t("pay.sub.block") : tx(`pay.sub.${a.level}`, "", { minutes: holdMinutes })}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <TrustBadge trust={a.trust} />
                    {a.sandbox_clock && <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">{t("pay.sandbox_clock", { time: a.local_time ?? "" })}</span>}
                  </div>
                  <div className="mt-3">
                    <SpeakButton source={{ kind: "payment", id: p.id }} autoPlay={a.level !== "low"} fallbackText={a.reasons.map((r) => pick(r.text, lang)).join(" ")} />
                  </div>
                </div>
              </div>
            </div>

            <div className="surface p-5">
              <h2 className="mb-3 font-display text-base font-semibold">{a.reasons.length ? t("pay.why_flagged") : t("pay.why_safe")}</h2>
              <ReasonList reasons={a.reasons} reassurance={a.reassurance} />
              <button className="mt-4 flex w-full items-center justify-between text-sm font-medium text-primary" onClick={() => setWhyOpen((v) => !v)} aria-expanded={whyOpen}>
                <span className="flex items-center gap-1.5">
                  <Info className="h-4 w-4" />
                  {t("pay.how_model_decided")}
                </span>
                <ChevronDown className={cn("h-4 w-4 transition", whyOpen && "rotate-180")} />
              </button>
              <AnimatePresence>
                {whyOpen && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                    <div className="mt-4 space-y-4 border-t pt-4">
                      <ContributionBars items={a.contributions} />
                      <dl className="grid grid-cols-2 gap-2 text-xs text-muted-foreground sm:grid-cols-4">
                        <div className="rounded-lg bg-muted/60 p-2">
                          <dt>{t("pay.model_probability")}</dt>
                          <dd className="font-semibold tabular text-foreground">{(a.probability * 100).toFixed(2)}%</dd>
                        </div>
                        <div className="rounded-lg bg-muted/60 p-2">
                          <dt>{t("pay.behaviour_score")}</dt>
                          <dd className="font-semibold tabular text-foreground">{(a.behaviour_score * 100).toFixed(1)}%</dd>
                        </div>
                        <div className="rounded-lg bg-muted/60 p-2">
                          <dt>{t("trust.label")}</dt>
                          <dd className="font-semibold tabular text-foreground">{a.payee_trust}/100</dd>
                        </div>
                        <div className="rounded-lg bg-muted/60 p-2">
                          <dt>{t("pay.model_version")}</dt>
                          <dd className="truncate font-mono text-[10px] text-foreground">{a.model_version}</dd>
                        </div>
                      </dl>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              {blocked ? (
                <>
                  <ReportButton upi={p.counterparty.upi_id} category="other" className="flex-1" />
                  <Button variant="outline" size="lg" className="flex-1" onClick={() => cancel.mutate()} disabled={cancel.isPending}>
                    <Ban className="mr-2 h-4 w-4" />
                    {t("pay.close_blocked")}
                  </Button>
                </>
              ) : (
                <>
                  <Button variant="outline" size="lg" className="flex-1" onClick={() => cancel.mutate()} disabled={cancel.isPending}>
                    {t("pay.cancel_payment")}
                  </Button>
                  <Button size="lg" className={cn("flex-1", a.level === "high" && "bg-danger text-danger-foreground hover:bg-danger/90")} onClick={() => setStep(needsIntent ? "intent" : "pin")}>
                    {needsIntent ? t("pay.to_safety_check") : t("pay.pay_amount", { amount: formatINR(p.amount) })}
                  </Button>
                </>
              )}
            </div>
          </motion.div>
        )}

        {step === "intent" && (
          <motion.div key="intent" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <IntentStep
              payment={p}
              onDone={(result, next) => {
                setIntentResult(result);
                setPayment(next);
                setUnderstood(false);
                setStep("warning");
              }}
            />
          </motion.div>
        )}

        {step === "warning" && (
          <motion.div key="warning" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
            {warning ? (
              <div className="rounded-2xl border-2 border-danger bg-danger-soft p-5">
                <p className="flex items-center gap-2 font-display text-lg font-semibold text-danger">
                  <ShieldAlert className="h-5 w-5" />
                  {warning.scam_type === "general" ? t("intent.warning.general") : t("intent.warning.typed", { type: pick(warning.name, lang) })}
                </p>
                <p className="mt-2 text-sm leading-relaxed">{pick(warning.advice, lang)}</p>
                <div className="mt-3">
                  <SpeakButton source={{ kind: "text", text: pick(warning.advice, lang) }} autoPlay fallbackText={pick(warning.advice, lang)} />
                </div>
              </div>
            ) : (
              <div className="surface p-5">
                <p className="font-display text-lg font-semibold">{t("intent.no_warning")}</p>
                <p className="mt-1 text-sm text-muted-foreground">{t("intent.no_warning_sub")}</p>
              </div>
            )}
            <div className="surface flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
              <span className="flex items-center gap-2">
                {t("intent.final_level")} <LevelBadge level={level} />
              </span>
              {level === "high" && <span className="text-muted-foreground">{t("intent.will_hold", { minutes: holdMinutes })}</span>}
            </div>
            {recommendCancel && (
              <label className="flex items-start gap-3 rounded-xl border p-3 text-sm">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-[hsl(var(--danger))]" checked={understood} onChange={(e) => setUnderstood(e.target.checked)} />
                <span>{t("intent.understand")}</span>
              </label>
            )}
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button size="lg" className={cn("flex-1", recommendCancel && "order-first")} variant={recommendCancel ? "default" : "outline"} onClick={() => cancel.mutate()} disabled={cancel.isPending}>
                {recommendCancel ? t("pay.cancel_recommended") : t("pay.cancel_payment")}
              </Button>
              <Button size="lg" variant={recommendCancel ? "outline" : "default"} className="flex-1" disabled={recommendCancel && !understood} onClick={() => setStep("pin")}>
                {level === "high" ? t("pay.continue_with_hold") : t("common.continue")}
              </Button>
            </div>
          </motion.div>
        )}

        {step === "pin" && (
          <motion.div key="pin" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <PinPad
              payment={p}
              level={level}
              holdMinutes={holdMinutes}
              onDone={(next) => {
                setPayment(next);
                if (next.status === "held") toast.warning(t("hold.started_toast", { minutes: next.hold?.hold_minutes ?? holdMinutes }));
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Steps({ step, needsIntent }: { step: Step; needsIntent: boolean }) {
  const { t } = useI18n();
  const all: { id: Step; label: string }[] = needsIntent
    ? [
        { id: "review", label: t("pay.step.review") },
        { id: "intent", label: t("pay.step.intent") },
        { id: "pin", label: t("pay.step.pin") },
      ]
    : [
        { id: "review", label: t("pay.step.review") },
        { id: "pin", label: t("pay.step.pin") },
      ];
  const idx = all.findIndex((s) => s.id === (step === "warning" ? "intent" : step));
  return (
    <ol className="flex items-center gap-1.5 text-xs" aria-label={t("pay.progress")}>
      {all.map((s, i) => (
        <li key={s.id} className="flex items-center gap-1.5">
          <span className={cn("grid h-5 w-5 place-items-center rounded-full text-[10px] font-bold", i <= idx ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground")}>{i + 1}</span>
          <span className={cn("hidden sm:inline", i === idx ? "font-medium" : "text-muted-foreground")}>{s.label}</span>
          {i < all.length - 1 && <span className="h-px w-4 bg-border" />}
        </li>
      ))}
    </ol>
  );
}

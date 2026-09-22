import { motion, useReducedMotion } from "motion/react";
import { Clock3, Loader2, PhoneCall, ShieldCheck, UserCheck } from "lucide-react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { ReasonList } from "@/components/risk/RiskBits";
import { GuideButton, SpeakButton } from "@/components/voice/SpeakButton";
import { formatCountdown, formatINR, formatTime } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Payment } from "@/lib/types";
import { useNow } from "@/lib/useNow";

export function HoldView({ payment, onCancel, cancelling }: { payment: Payment; onCancel: () => void; cancelling: boolean }) {
  const { t, lang } = useI18n();
  const reduce = useReducedMotion();
  const now = useNow(1000);
  const h = payment.hold!;
  const end = new Date(h.hold_until).getTime();
  const total = h.hold_minutes * 60_000;
  const left = Math.max(0, end - now);
  const progress = total ? 1 - left / total : 1;
  const R = 70;
  const C = 2 * Math.PI * R;

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div className="surface overflow-hidden p-6 text-center">
        <div className="flex justify-end">
          <GuideButton screen="hold" />
        </div>
        <div className="relative mx-auto h-44 w-44">
          <svg viewBox="0 0 160 160" className="h-full w-full -rotate-90">
            <circle cx="80" cy="80" r={R} fill="none" stroke="hsl(var(--muted))" strokeWidth="10" />
            <motion.circle
              cx="80"
              cy="80"
              r={R}
              fill="none"
              stroke="var(--status-warning)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={C}
              animate={{ strokeDashoffset: C * progress }}
              transition={reduce ? { duration: 0 } : { duration: 0.8, ease: "linear" }}
            />
          </svg>
          <div className="absolute inset-0 grid place-items-center">
            <div>
              <Clock3 className="mx-auto h-5 w-5 text-caution" />
              <p className="mt-1 font-display text-3xl font-semibold tabular" aria-live="polite">
                {formatCountdown(left)}
              </p>
              <p className="text-xs text-muted-foreground">{t("hold.left")}</p>
            </div>
          </div>
        </div>
        <h1 className="mt-4 font-display text-2xl font-semibold">{t("hold.title")}</h1>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
          {t("hold.subtitle", { amount: formatINR(payment.amount), name: payment.counterparty.name, time: formatTime(h.hold_until, lang) })}
        </p>
        {h.needs_approval && (
          <p className="mx-auto mt-3 flex max-w-sm items-center justify-center gap-2 rounded-lg bg-muted px-3 py-2 text-sm">
            <UserCheck className="h-4 w-4 text-primary" />
            {h.approval_status === "pending" ? t("hold.waiting_approval") : t(`hold.approval.${h.approval_status}` as "hold.approval.approved")}
          </p>
        )}
        <div className="mt-4 flex justify-center">
          <SpeakButton source={{ kind: "payment", id: payment.id }} />
        </div>
      </div>

      <div className="surface p-5">
        <h2 className="mb-3 flex items-center gap-2 font-display text-base font-semibold">
          <PhoneCall className="h-4 w-4 text-primary" />
          {t("hold.use_the_time")}
        </h2>
        <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
          <li>{t("hold.tip1")}</li>
          <li>{t("hold.tip2")}</li>
          <li>{t("hold.tip3")}</li>
        </ul>
      </div>

      {payment.assessment && (
        <div className="surface p-5">
          <h2 className="mb-3 font-display text-base font-semibold">{t("pay.why_flagged")}</h2>
          <ReasonList reasons={payment.assessment.reasons} />
        </div>
      )}

      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button size="lg" variant="default" className="w-full bg-danger text-danger-foreground hover:bg-danger/90" disabled={cancelling}>
            {cancelling ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
            {t("hold.cancel")}
          </Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("hold.cancel_confirm_title")}</AlertDialogTitle>
            <AlertDialogDescription>{t("hold.cancel_confirm_body", { amount: formatINR(payment.amount) })}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("hold.keep_waiting")}</AlertDialogCancel>
            <AlertDialogAction onClick={onCancel}>{t("hold.cancel")}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <p className="text-center text-xs text-muted-foreground">{t("hold.auto_release")}</p>
    </div>
  );
}

import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { Ban, CheckCircle2, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LevelBadge } from "@/components/risk/RiskBits";
import { formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Payment } from "@/lib/types";
import { BackHome, ReportButton } from "@/pages/pay/shared";

export function SuccessView({ payment }: { payment: Payment }) {
  const { t, lang } = useI18n();
  return (
    <div className="mx-auto max-w-md text-center">
      <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 200, damping: 14 }} className="mx-auto grid h-24 w-24 place-items-center rounded-full bg-safe-soft">
        <motion.span initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}>
          <CheckCircle2 className="h-14 w-14 text-safe" />
        </motion.span>
      </motion.div>
      <h1 className="mt-5 font-display text-2xl font-semibold">{t("done.paid_title")}</h1>
      <p className="mt-1 font-display text-4xl font-semibold tabular">{formatINR(payment.amount)}</p>
      <p className="mt-1 text-muted-foreground">{t("done.to", { name: payment.counterparty.name })}</p>
      <dl className="surface mt-6 space-y-2 p-4 text-left text-sm">
        <div className="flex justify-between">
          <dt className="text-muted-foreground">{t("done.reference")}</dt>
          <dd className="font-mono">{payment.reference}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted-foreground">{t("done.when")}</dt>
          <dd>{formatDateTime(payment.completed_at ?? payment.created_at, lang)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted-foreground">{t("risk.level")}</dt>
          <dd>
            <LevelBadge level={payment.level} />
          </dd>
        </div>
        {payment.status_reason === "released_after_hold" && <p className="pt-1 text-xs text-muted-foreground">{t("done.released_after_hold")}</p>}
        {payment.status_reason === "approved_by_trusted_contact" && <p className="pt-1 text-xs text-muted-foreground">{t("done.approved_by_contact")}</p>}
      </dl>
      <div className="mt-6 flex gap-2">
        <Button asChild variant="outline" size="lg" className="flex-1">
          <Link to={`/app/history/${payment.id}`}>{t("done.details")}</Link>
        </Button>
        <BackHome />
      </div>
    </div>
  );
}

export function CancelledView({ payment }: { payment: Payment }) {
  const { t, tx } = useI18n();
  const blocked = payment.status === "blocked" || payment.assessment?.action === "block";
  const protectedByUs = payment.level && payment.level !== "low";
  return (
    <div className="mx-auto max-w-md text-center">
      <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 200, damping: 14 }} className="mx-auto grid h-24 w-24 place-items-center rounded-full bg-primary/10">
        {blocked ? <Ban className="h-12 w-12 text-danger" /> : <ShieldCheck className="h-12 w-12 text-primary" />}
      </motion.div>
      <h1 className="mt-5 font-display text-2xl font-semibold">{blocked ? t("done.blocked_title") : t("done.cancelled_title")}</h1>
      <p className="mt-2 text-muted-foreground">{protectedByUs ? t("done.cancelled_protected", { amount: formatINR(payment.amount) }) : t("done.cancelled_plain")}</p>
      {payment.status_reason && <p className="mt-2 text-xs text-muted-foreground">{tx(`reason.${payment.status_reason}`, "")}</p>}
      <div className="mt-6 flex flex-col gap-2 sm:flex-row">
        {protectedByUs && <ReportButton upi={payment.counterparty.upi_id} category={payment.intent?.matched_scam_type ?? "other"} className="flex-1" />}
        <BackHome />
      </div>
    </div>
  );
}

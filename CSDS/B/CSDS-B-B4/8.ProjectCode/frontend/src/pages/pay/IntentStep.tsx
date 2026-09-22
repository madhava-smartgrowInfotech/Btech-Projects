import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Briefcase, Gift, HelpCircle, IdCard, Landmark, Loader2, Receipt, RotateCcw, ShoppingBag, TrendingUp, Users } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { IntentResult, Payment } from "@/lib/types";
import { cn } from "@/lib/utils";

const PURPOSE_ICON: Record<string, typeof Users> = {
  family_friend: Users,
  shopping: ShoppingBag,
  bill: Receipt,
  refund: RotateCcw,
  prize: Gift,
  kyc: IdCard,
  job: Briefcase,
  loan: Landmark,
  investment: TrendingUp,
  other: HelpCircle,
};

function YesNo({ value, onChange, label }: { value: boolean | null; onChange: (v: boolean) => void; label: string }) {
  const { t } = useI18n();
  return (
    <fieldset className="rounded-xl border p-4">
      <legend className="px-1 text-sm font-medium">{label}</legend>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {[true, false].map((v) => (
          <button
            key={String(v)}
            type="button"
            onClick={() => onChange(v)}
            className={cn("rounded-lg border px-3 py-2.5 text-sm font-medium transition", value === v ? "border-primary bg-primary text-primary-foreground" : "hover:border-primary/40")}
            aria-pressed={value === v}
          >
            {v ? t("common.yes") : t("common.no")}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function IntentStep({ payment, onDone }: { payment: Payment; onDone: (result: IntentResult, payment: Payment) => void }) {
  const { t, tx } = useI18n();
  const questions = payment.questions ?? [];
  const options = questions.find((q) => q.id === "purpose")?.options ?? Object.keys(PURPOSE_ICON);
  const [purpose, setPurpose] = useState<string | null>(null);
  const [asked, setAsked] = useState<boolean | null>(null);
  const [verified, setVerified] = useState<boolean | null>(null);
  const [advance, setAdvance] = useState<boolean | null>(null);
  const showVerified = !!purpose && questions.some((q) => q.id === "verified_by_call" && q.only_for_purpose?.includes(purpose));
  const showAdvance = !!purpose && questions.some((q) => q.id === "advance_to_online_seller" && q.only_for_purpose?.includes(purpose));
  const ready = purpose && asked !== null && (!showVerified || verified !== null) && (!showAdvance || advance !== null);

  const submit = useMutation({
    mutationFn: async () =>
      (
        await api.post<{ result: IntentResult; payment: Payment }>(`/payments/${payment.id}/intent`, {
          purpose,
          asked_by_someone: asked,
          verified_by_call: showVerified ? verified : null,
          advance_to_online_seller: showAdvance ? advance : null,
        })
      ).data,
    onSuccess: (d) => onDone(d.result, d.payment),
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  return (
    <div className="space-y-4">
      <div className="surface p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-xl font-semibold">{t("intent.title")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{t("intent.subtitle")}</p>
          </div>
          <GuideButton screen="intent" />
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {options.map((o, i) => {
            const Icon = PURPOSE_ICON[o] ?? HelpCircle;
            return (
              <motion.button
                key={o}
                type="button"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.03 * i }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setPurpose(o)}
                className={cn(
                  "flex min-h-[4.5rem] items-center gap-2.5 rounded-xl border p-3 text-left text-sm transition",
                  purpose === o ? "border-primary bg-primary/10 ring-2 ring-primary/25" : "hover:border-primary/40",
                )}
                aria-pressed={purpose === o}
              >
                <Icon className={cn("h-5 w-5 shrink-0", purpose === o ? "text-primary" : "text-muted-foreground")} />
                <span className="leading-tight">{tx(`purpose.${o}`, o)}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {purpose && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
          <YesNo value={asked} onChange={setAsked} label={t("intent.q.asked_by_someone")} />
          {showVerified && <YesNo value={verified} onChange={setVerified} label={t("intent.q.verified_by_call")} />}
          {showAdvance && <YesNo value={advance} onChange={setAdvance} label={t("intent.q.advance_to_online_seller")} />}
        </motion.div>
      )}

      <Button size="lg" className="w-full" disabled={!ready || submit.isPending} onClick={() => submit.mutate()}>
        {submit.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {t("intent.submit")}
      </Button>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, useAnimationControls } from "motion/react";
import { Clock3, Delete, Loader2, Lock } from "lucide-react";
import { api, apiError } from "@/lib/api";
import { formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Level, Payment } from "@/lib/types";
import { cn } from "@/lib/utils";

export function PinPad({ payment, level, holdMinutes, onDone }: { payment: Payment; level: Level; holdMinutes: number; onDone: (p: Payment) => void }) {
  const { t, tx } = useI18n();
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const shake = useAnimationControls();

  const confirm = useMutation({
    mutationFn: async (value: string) => (await api.post<Payment>(`/payments/${payment.id}/confirm`, { pin: value })).data,
    onSuccess: onDone,
    onError: (err) => {
      const d = apiError(err);
      setError(tx(`error.${d.code}`, d.message));
      setPin("");
      void shake.start({ x: [0, -10, 10, -8, 8, 0], transition: { duration: 0.4 } });
    },
  });

  useEffect(() => {
    if (pin.length === 4 && !confirm.isPending) confirm.mutate(pin);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pin]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (/^\d$/.test(e.key)) setPin((p) => (p.length < 4 ? p + e.key : p));
      if (e.key === "Backspace") setPin((p) => p.slice(0, -1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const press = (d: string) => {
    setError(null);
    setPin((p) => (p.length < 4 ? p + d : p));
  };

  return (
    <div className="surface mx-auto max-w-sm p-6 text-center">
      <Lock className="mx-auto h-6 w-6 text-primary" />
      <h2 className="mt-2 font-display text-xl font-semibold">{t("pin.title")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("pin.subtitle", { amount: formatINR(payment.amount), name: payment.counterparty.name })}</p>
      {level === "high" && (
        <p className="mt-3 flex items-center justify-center gap-1.5 rounded-lg bg-caution-soft px-3 py-2 text-xs font-medium text-caution">
          <Clock3 className="h-3.5 w-3.5" />
          {t("intent.will_hold", { minutes: holdMinutes })}
        </p>
      )}
      <motion.div animate={shake} className="my-6 flex justify-center gap-4" aria-live="polite" aria-label={t("pin.entered", { n: pin.length })}>
        {[0, 1, 2, 3].map((i) => (
          <motion.span
            key={i}
            animate={{ scale: pin.length > i ? 1.15 : 1 }}
            className={cn("h-4 w-4 rounded-full border-2", pin.length > i ? "border-primary bg-primary" : "border-muted-foreground/40")}
          />
        ))}
      </motion.div>
      {error && (
        <p role="alert" className="-mt-2 mb-3 text-sm text-danger">
          {error}
        </p>
      )}
      <div className="grid grid-cols-3 gap-2">
        {["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "del"].map((k) =>
          k === "" ? (
            <span key="blank" />
          ) : (
            <motion.button
              key={k}
              type="button"
              whileTap={{ scale: 0.92 }}
              disabled={confirm.isPending}
              onClick={() => (k === "del" ? setPin((p) => p.slice(0, -1)) : press(k))}
              className="h-14 rounded-xl bg-muted text-xl font-semibold transition hover:bg-accent disabled:opacity-50"
              aria-label={k === "del" ? t("pin.delete") : k}
            >
              {k === "del" ? <Delete className="mx-auto h-5 w-5" /> : k}
            </motion.button>
          ),
        )}
      </div>
      {confirm.isPending && (
        <p className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          {t("pin.processing")}
        </p>
      )}
      <p className="mt-4 text-xs text-muted-foreground">{t("pin.sandbox_hint")}</p>
    </div>
  );
}

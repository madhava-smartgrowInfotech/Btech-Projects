import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { AlertTriangle, CheckCircle2, ClipboardPaste, Flag, Link2, Loader2, MessageSquareWarning, Phone, ShieldAlert, Wallet } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState, ListSkeleton, PageHeader } from "@/components/common/States";
import { HighlightedText } from "@/components/risk/HighlightedText";
import { pick } from "@/components/risk/RiskBits";
import { GuideButton, SpeakButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { SmsResult } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SampleSms {
  id: string;
  language: string;
  kind: "scam" | "genuine";
  text: string;
}

const VERDICT = {
  scam: { icon: ShieldAlert, cls: "border-danger bg-danger-soft text-danger", bar: "var(--status-critical)" },
  suspicious: { icon: AlertTriangle, cls: "border-caution bg-caution-soft text-caution", bar: "var(--status-warning)" },
  safe: { icon: CheckCircle2, cls: "border-safe bg-safe-soft text-safe", bar: "var(--status-good)" },
} as const;

function Meter({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs text-muted-foreground">
        <span>{label}</span>
        <span className="tabular">{Math.round(value * 100)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <motion.div className="h-full rounded-full" style={{ background: color }} initial={{ width: 0 }} animate={{ width: `${value * 100}%` }} transition={{ duration: 0.6 }} />
      </div>
    </div>
  );
}

function ResultCard({ r }: { r: SmsResult }) {
  const { t, tx, lang } = useI18n();
  const qc = useQueryClient();
  const v = VERDICT[r.verdict];
  const report = useMutation({
    mutationFn: async () => (await api.post<{ reported: string[] }>(`/sms/${r.id}/report`)).data,
    onSuccess: (d) => {
      toast.success(d.reported.length ? t("sms.reported", { ids: d.reported.join(", ") }) : t("sms.nothing_to_report"));
      qc.invalidateQueries({ queryKey: ["sms"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <div className={cn("rounded-2xl border-2 p-5", v.cls)}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="flex items-center gap-2 font-display text-xl font-semibold">
              <v.icon className="h-6 w-6" />
              {t(`sms.verdict.${r.verdict}`)}
            </p>
            {r.scam_type_name && <p className="mt-1 text-sm font-medium text-foreground">{t("sms.type", { type: pick(r.scam_type_name, lang) })}</p>}
          </div>
          <span className="rounded-full bg-background/70 px-2.5 py-1 text-xs font-semibold text-foreground tabular">{Math.round(r.probability * 100)}%</span>
        </div>
        {r.advice && <p className="mt-3 text-sm leading-relaxed text-foreground">{pick(r.advice, lang)}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <SpeakButton source={{ kind: "sms", id: r.id }} autoPlay={r.verdict !== "safe"} fallbackText={r.advice ? pick(r.advice, lang) : ""} variant="secondary" />
          {r.verdict !== "safe" && r.entities.upi_ids.length > 0 && (
            <Button size="sm" variant="secondary" onClick={() => report.mutate()} disabled={report.isPending || report.isSuccess}>
              <Flag className="mr-1.5 h-4 w-4" />
              {report.isSuccess ? t("report.done") : t("sms.report_ids")}
            </Button>
          )}
        </div>
      </div>

      <div className="surface space-y-4 p-5">
        <div>
          <p className="mb-2 text-sm font-semibold">{t("sms.message")}</p>
          <div className="rounded-xl bg-muted/50 p-3 text-sm">
            <HighlightedText text={r.text} highlights={r.highlights} />
          </div>
          {r.highlights.length > 0 && <p className="mt-2 text-xs text-muted-foreground">{t("sms.highlight_legend")}</p>}
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <Meter label={t("sms.model_score")} value={r.model_probability ?? 0} color="var(--series-1)" />
          <Meter label={t("sms.rules_score")} value={r.rules_score ?? 0} color="var(--series-2)" />
        </div>
        {r.signals.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-semibold">{t("sms.signals")}</p>
            <ul className="flex flex-wrap gap-1.5">
              {r.signals.map((s) => (
                <li key={s.rule} className="rounded-full border px-2.5 py-1 text-xs">
                  {tx(`rule.${s.rule}`, s.rule)}
                </li>
              ))}
            </ul>
          </div>
        )}
        {(r.entities.upi_ids.length > 0 || r.entities.urls.length > 0 || r.entities.phones.length > 0 || r.entities.amounts.length > 0) && (
          <div>
            <p className="mb-2 text-sm font-semibold">{t("sms.found")}</p>
            <ul className="space-y-1.5 text-sm">
              {r.linked_accounts.map((u) => (
                <li key={u.upi_id} className="flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono">{u.upi_id}</span>
                  {u.name && <span className="text-muted-foreground">({u.name})</span>}
                  {r.verdict !== "safe" && <span className="text-xs text-danger">{t("sms.linked_warning")}</span>}
                </li>
              ))}
              {r.entities.urls.map((u) => (
                <li key={u} className="flex items-center gap-2 break-all">
                  <Link2 className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="font-mono text-xs">{u}</span>
                </li>
              ))}
              {r.entities.phones.map((p) => (
                <li key={p} className="flex items-center gap-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono">{p}</span>
                </li>
              ))}
              {r.entities.amounts.length > 0 && <li className="text-muted-foreground">{t("sms.amounts", { list: r.entities.amounts.map((a) => formatINR(a)).join(", ") })}</li>}
            </ul>
          </div>
        )}
        <p className="text-xs text-muted-foreground">{t("sms.language_detected", { lang: tx(`lang.${r.language}`, r.language) })}</p>
      </div>
    </motion.div>
  );
}

export default function SmsCheck() {
  const { t, tx, lang } = useI18n();
  const qc = useQueryClient();
  const [text, setText] = useState("");
  const [result, setResult] = useState<SmsResult | null>(null);
  const samples = useQuery({ queryKey: ["sandbox", "samples"], queryFn: async () => (await api.get<{ sms: SampleSms[] }>("/sandbox/samples")).data });
  const history = useQuery({ queryKey: ["sms", "history"], queryFn: async () => (await api.get<{ items: SmsResult[] }>("/sms/history", { params: { limit: 8 } })).data });
  const check = useMutation({
    mutationFn: async (value: string) => (await api.post<SmsResult>("/sms/check", { text: value })).data,
    onSuccess: (r) => {
      setResult(r);
      qc.invalidateQueries({ queryKey: ["sms", "history"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  const paste = async () => {
    try {
      const v = await navigator.clipboard.readText();
      if (v) setText(v);
    } catch {
      toast.message(t("sms.paste_blocked"));
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title={t("nav.sms")} subtitle={t("sms.subtitle")} actions={<GuideButton screen="sms" />} />
      <div className="surface space-y-3 p-5">
        <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={5} placeholder={t("sms.placeholder")} aria-label={t("sms.placeholder")} className="text-base" />
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => check.mutate(text)} disabled={text.trim().length < 3 || check.isPending}>
            {check.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <MessageSquareWarning className="mr-2 h-4 w-4" />}
            {t("sms.check")}
          </Button>
          <Button variant="outline" onClick={paste}>
            <ClipboardPaste className="mr-2 h-4 w-4" />
            {t("sms.paste")}
          </Button>
        </div>
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">{t("sms.try_sample")}</p>
          <div className="flex flex-wrap gap-1.5">
            {samples.data?.sms.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setText(s.text);
                  check.mutate(s.text);
                }}
                className={cn("rounded-full border px-2.5 py-1 text-xs transition hover:border-primary/50", s.kind === "scam" ? "border-danger/30" : "border-safe/30")}
              >
                {tx(`sms.sample.${s.id}`, s.id)}
              </button>
            ))}
          </div>
        </div>
      </div>

      <AnimatePresence mode="wait">{result && <div key={result.id} className="mt-5"><ResultCard r={result} /></div>}</AnimatePresence>

      <section className="mt-8">
        <h2 className="mb-3 font-display text-base font-semibold">{t("sms.history")}</h2>
        {history.isLoading ? (
          <ListSkeleton rows={3} />
        ) : history.data?.items.length ? (
          <ul className="space-y-2">
            {history.data.items.map((h) => {
              const v = VERDICT[h.verdict];
              return (
                <li key={h.id}>
                  <button className="surface flex w-full items-start gap-3 p-3 text-left transition hover:shadow-lift" onClick={() => setResult(h)}>
                    <v.icon className={cn("mt-0.5 h-5 w-5 shrink-0", v.cls.split(" ").pop())} />
                    <span className="min-w-0 flex-1">
                      <span className="line-clamp-2 text-sm">{h.text}</span>
                      <span className="text-xs text-muted-foreground">
                        {formatDateTime(h.created_at, lang)} · {t(`sms.verdict.${h.verdict}`)}
                        {h.scam_type_name ? ` · ${pick(h.scam_type_name, lang)}` : ""}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState title={t("sms.no_history")} description={t("sms.no_history_hint")} />
        )}
      </section>
    </div>
  );
}

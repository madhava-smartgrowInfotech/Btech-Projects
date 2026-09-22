import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, Clock3, MessageCircleQuestion, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CardSkeleton, ErrorState } from "@/components/common/States";
import { ContributionBars, LevelBadge, PartyRow, ReasonList, RiskGauge, StatusBadge, TrustBadge, pick } from "@/components/risk/RiskBits";
import { SpeakButton } from "@/components/voice/SpeakButton";
import { api } from "@/lib/api";
import { formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Payment } from "@/lib/types";

export default function HistoryDetail() {
  const { id } = useParams();
  const { t, tx, lang } = useI18n();
  const navigate = useNavigate();
  const q = useQuery({ queryKey: ["payment", Number(id)], queryFn: async () => (await api.get<Payment>(`/payments/${id}`)).data });

  if (q.isLoading) return <CardSkeleton rows={6} />;
  if (q.isError || !q.data) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const p = q.data;
  const a = p.assessment;

  const timeline = [
    { icon: ShieldCheck, label: t("detail.t.assessed", { score: a?.score ?? "–" }), at: a?.created_at },
    ...(p.intent ? [{ icon: MessageCircleQuestion, label: t("detail.t.intent", { purpose: tx(`purpose.${p.intent.purpose}`, p.intent.purpose) }), at: undefined as string | undefined }] : []),
    ...(p.hold ? [{ icon: Clock3, label: t("detail.t.held", { minutes: p.hold.hold_minutes }), at: p.hold.hold_until }] : []),
    { icon: CheckCircle2, label: tx(`status.${p.status}`, p.status) + (p.status_reason ? ` · ${tx(`reason.${p.status_reason}`, "")}` : ""), at: p.completed_at ?? undefined },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
        <ArrowLeft className="mr-1 h-4 w-4" />
        {t("common.back")}
      </Button>

      <div className="surface p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <PartyRow party={p.counterparty} className="min-w-0 flex-1" />
          <div className="text-right">
            <p className="font-display text-2xl font-semibold tabular">
              {p.direction === "received" ? "+" : "−"}
              {formatINR(p.amount)}
            </p>
            <StatusBadge status={p.status} />
          </div>
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <div>
            <dt className="text-xs text-muted-foreground">{t("done.reference")}</dt>
            <dd className="font-mono text-xs">{p.reference}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">{t("done.when")}</dt>
            <dd>{formatDateTime(p.created_at, lang)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">{t("detail.channel")}</dt>
            <dd>{tx(`channel.${p.channel}`, p.channel)}</dd>
          </div>
          {p.note && (
            <div>
              <dt className="text-xs text-muted-foreground">{t("send.note")}</dt>
              <dd className="truncate">{p.note}</dd>
            </div>
          )}
        </dl>
        {p.status === "held" && (
          <Button asChild className="mt-4 w-full">
            <Link to={`/app/pay/${p.id}`}>{t("detail.open_hold")}</Link>
          </Button>
        )}
      </div>

      {p.direction === "received" ? (
        <p className="surface p-5 text-sm text-muted-foreground">{t("detail.received_note")}</p>
      ) : a ? (
        <>
          <div className="grid gap-4 md:grid-cols-[240px_1fr]">
            <div className="surface p-5">
              <RiskGauge score={a.score} level={a.final_level} size={200} />
              <div className="mt-3 flex flex-wrap justify-center gap-2">
                <TrustBadge trust={a.trust} />
                {a.final_level !== a.level && (
                  <span className="text-xs text-muted-foreground">
                    {t("detail.escalated")} <LevelBadge level={a.final_level} />
                  </span>
                )}
              </div>
              <div className="mt-3 flex justify-center">
                <SpeakButton source={{ kind: "payment", id: p.id }} fallbackText={a.reasons.map((r) => pick(r.text, lang)).join(" ")} />
              </div>
            </div>
            <div className="surface p-5">
              <h2 className="mb-3 font-display text-base font-semibold">{t("detail.reasons")}</h2>
              <ReasonList reasons={a.reasons} reassurance={a.reassurance} />
            </div>
          </div>
          <div className="surface p-5">
            <h2 className="mb-1 font-display text-base font-semibold">{t("detail.shap_title")}</h2>
            <p className="mb-4 text-xs text-muted-foreground">{t("detail.shap_sub")}</p>
            <ContributionBars items={a.contributions} max={12} />
          </div>
          {p.intent?.warning && (
            <div className="rounded-2xl border border-danger/40 bg-danger-soft p-5 text-sm">
              <p className="font-semibold text-danger">{t("intent.warning.typed", { type: pick(p.intent.warning.name, lang) || t("intent.warning.general") })}</p>
              <p className="mt-1">{pick(p.intent.warning.advice, lang)}</p>
            </div>
          )}
        </>
      ) : null}

      <div className="surface p-5">
        <h2 className="mb-3 font-display text-base font-semibold">{t("detail.timeline")}</h2>
        <ol className="relative space-y-4 border-l pl-5">
          {timeline.map((s, i) => (
            <li key={i} className="relative">
              <span className="absolute -left-[29px] grid h-6 w-6 place-items-center rounded-full border bg-card">
                <s.icon className="h-3.5 w-3.5 text-primary" />
              </span>
              <p className="text-sm">{s.label}</p>
              {s.at && <p className="text-xs text-muted-foreground">{formatDateTime(s.at, lang)}</p>}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

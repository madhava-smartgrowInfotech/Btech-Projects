import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, CheckCircle2, Database, Info } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HBar } from "@/components/charts/HBar";
import { CardSkeleton, ErrorState, PageHeader } from "@/components/common/States";
import { api } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Metrics = Record<string, any>;
interface Split {
  n: number;
  positives: number;
  prevalence: number;
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  pr_auc: number;
  roc_auc: number | null;
}

function Tile({ label, value, hint, strong = false }: { label: string; value: string; hint?: string; strong?: boolean }) {
  return (
    <div className={cn("rounded-xl border p-3", strong && "border-primary/40 bg-primary/5")}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 font-display text-xl font-semibold tabular">{value}</p>
      {hint && <p className="text-2xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

function SplitTiles({ s }: { s: Split }) {
  const { t } = useI18n();
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      <Tile label="PR-AUC" value={s.pr_auc.toFixed(3)} hint={t("models.base_rate", { rate: formatPercent(s.prevalence, 2) })} strong />
      <Tile label="ROC-AUC" value={s.roc_auc?.toFixed(3) ?? "–"} />
      <Tile label={t("models.precision")} value={s.precision.toFixed(3)} />
      <Tile label={t("models.recall")} value={s.recall.toFixed(3)} />
      <Tile label="F1" value={s.f1.toFixed(3)} />
    </div>
  );
}

function CompareTable({ models, deployed }: { models: Record<string, { test: Split }>; deployed: string }) {
  const { t } = useI18n();
  return (
    <div className="overflow-x-auto rounded-xl border">
      <table className="w-full min-w-[520px] text-sm">
        <thead className="bg-muted text-xs text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left font-medium">{t("models.model")}</th>
            {["PR-AUC", "ROC-AUC", t("models.precision"), t("models.recall"), "F1"].map((h) => (
              <th key={h} className="px-3 py-2 text-right font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(models).map(([name, m]) => (
            <tr key={name} className={cn("border-t", deployed.startsWith(name) && "bg-primary/5 font-medium")}>
              <td className="px-3 py-2">
                {name} {deployed.startsWith(name) && <CheckCircle2 className="ml-1 inline h-3.5 w-3.5 text-primary" />}
              </td>
              {[m.test.pr_auc, m.test.roc_auc ?? 0, m.test.precision, m.test.recall, m.test.f1].map((v, i) => (
                <td key={i} className="px-3 py-2 text-right tabular">
                  {v.toFixed(3)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Plots({ urls, onOpen }: { urls: string[]; onOpen: (u: string) => void }) {
  const { t, tx } = useI18n();
  return (
    <section className="surface p-5">
      <h2 className="mb-3 font-display text-base font-semibold">{t("models.plots")}</h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
        {urls.map((u) => {
          const name = u.split("/").pop()!.replace(".png", "");
          return (
            <button key={u} onClick={() => onOpen(u)} className="group overflow-hidden rounded-xl border bg-white text-left transition hover:shadow-lift">
              <img src={u} alt={tx(`plot.${name}`, name)} loading="lazy" className="aspect-[4/3] w-full object-contain p-1" />
              <p className="border-t bg-card px-2 py-1.5 text-xs text-card-foreground">{tx(`plot.${name}`, name.replace(/_/g, " "))}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function Header({ m }: { m: Metrics }) {
  const { t } = useI18n();
  return (
    <div className="surface space-y-2 p-5 text-sm">
      <p className="flex items-center gap-2 font-display text-base font-semibold">
        <BrainCircuit className="h-4 w-4 text-primary" />
        {m.model} · <span className="text-primary">{m.deployed}</span>
      </p>
      <p className="text-muted-foreground">
        <Database className="mr-1 inline h-3.5 w-3.5" />
        {m.dataset?.name ?? Object.values(m.dataset?.sources ?? {}).join(" + ")}
      </p>
      <p className="text-muted-foreground">
        <Info className="mr-1 inline h-3.5 w-3.5" />
        {m.dataset?.split}
      </p>
      <p className="text-xs text-muted-foreground">
        {t("models.run", { run: m.run, version: m.version ?? "", date: (m.created_at ?? "").slice(0, 10) })}
      </p>
    </div>
  );
}

export default function ModelPerformance() {
  const { t, tx } = useI18n();
  const [open, setOpen] = useState<string | null>(null);
  const q = useQuery({ queryKey: ["models"], queryFn: async () => (await api.get<{ models: Record<string, Metrics | null> }>("/models")).data, staleTime: 300_000 });

  if (q.isLoading) return <CardSkeleton rows={8} />;
  if (q.isError || !q.data) return <ErrorState error={q.error} onRetry={() => q.refetch()} />;
  const { risk, behaviour, sms, sms_comparison: cmp, profile } = q.data.models;
  const pct = (v: number) => formatPercent(v, 1);

  return (
    <div className="space-y-5">
      <PageHeader title={t("nav.models")} subtitle={t("models.subtitle")} />
      <Tabs defaultValue="risk">
        <TabsList className="flex h-auto flex-wrap justify-start">
          <TabsTrigger value="risk">{t("models.tab.risk")}</TabsTrigger>
          <TabsTrigger value="behaviour">{t("models.tab.behaviour")}</TabsTrigger>
          <TabsTrigger value="sms">{t("models.tab.sms")}</TabsTrigger>
          <TabsTrigger value="data">{t("models.tab.data")}</TabsTrigger>
        </TabsList>

        {risk && (
          <TabsContent value="risk" className="space-y-4">
            <Header m={risk} />
            <SplitTiles s={risk.models.XGBoost.test} />
            <div className="surface p-5">
              <h2 className="mb-1 font-display text-base font-semibold">{t("models.policy_title")}</h2>
              <p className="mb-3 text-xs text-muted-foreground">{t("models.policy_sub", { medium: risk.policy.medium_score, high: risk.policy.high_score })}</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                <Tile label={t("models.scams_checked")} value={pct(risk.policy.test.scams_reaching_medium_or_high)} strong />
                <Tile label={t("models.scams_held")} value={pct(risk.policy.test.scams_reaching_high_hold)} strong />
                <Tile label={t("models.genuine_straight")} value={pct(risk.policy.test.genuine_payments_low)} />
                <Tile label={t("models.genuine_asked")} value={pct(risk.policy.test.genuine_payments_asked_intent_medium)} />
                <Tile label={t("models.genuine_held")} value={pct(risk.policy.test.genuine_payments_held_high)} />
              </div>
            </div>
            <CompareTable models={risk.models} deployed={risk.deployed} />
            <div className="grid gap-4 lg:grid-cols-2">
              <HBar
                title={t("models.per_type")}
                subtitle={t("models.per_type_sub")}
                valueLabel={t("models.share_checked")}
                format={(v) => pct(v)}
                data={Object.entries(risk.per_scam_type_test as Record<string, { caught_medium_or_high: number }>)
                  .filter(([k]) => k !== "none")
                  .map(([k, v]) => ({ label: tx(`scam.${k}`, k), value: v.caught_medium_or_high }))
                  .sort((a, b) => b.value - a.value)}
              />
              <HBar
                title={t("models.ablation")}
                subtitle={t("models.ablation_sub")}
                valueLabel="PR-AUC"
                highlight={tx("ablation.all signals (deployed)", "all signals (deployed)")}
                labelWidth={190}
                data={Object.entries(risk.ablation_test_pr_auc as Record<string, number>).map(([k, v]) => ({ label: tx(`ablation.${k}`, k), value: v }))}
              />
            </div>
            <HBar
              title={t("models.shap")}
              subtitle={t("models.shap_sub")}
              valueLabel={t("models.mean_shap")}
              labelWidth={180}
              data={Object.entries(risk.shap_mean_abs as Record<string, number>)
                .map(([k, v]) => ({ label: tx(`feature.${k}`, k), value: v }))
                .sort((a, b) => b.value - a.value)
                .slice(0, 12)}
            />
            <Plots urls={risk.plot_urls ?? []} onOpen={setOpen} />
          </TabsContent>
        )}

        {behaviour && (
          <TabsContent value="behaviour" className="space-y-4">
            <Header m={behaviour} />
            <SplitTiles s={behaviour.models.XGBoost.test} />
            <CompareTable models={behaviour.models} deployed={behaviour.deployed} />
            <div className="grid gap-2 sm:grid-cols-3">
              <Tile label={t("models.full_feature")} value={behaviour.full_feature_reference.test.pr_auc.toFixed(3)} hint={t("models.full_feature_hint")} />
              <Tile label={t("models.no_gps")} value={behaviour.models.XGBoost.test_without_gps.pr_auc.toFixed(3)} hint={t("models.no_gps_hint")} />
              <Tile label={t("models.drift")} value={`${behaviour.drift_check.pr_auc_june_before_drift.toFixed(3)} → ${behaviour.drift_check.pr_auc_jul_sep_after_drift.toFixed(3)}`} hint={t("models.drift_hint")} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <HBar title={t("models.by_month")} valueLabel="PR-AUC" data={Object.entries(behaviour.pr_auc_by_month as Record<string, number>).map(([k, v]) => ({ label: k, value: v }))} labelWidth={70} />
              <HBar title={t("models.shap")} valueLabel={t("models.mean_shap")} labelWidth={220} data={Object.entries(behaviour.shap_mean_abs as Record<string, number>).map(([k, v]) => ({ label: k, value: v })).sort((a, b) => b.value - a.value)} />
            </div>
            <Plots urls={behaviour.plot_urls ?? []} onOpen={setOpen} />
          </TabsContent>
        )}

        {sms && (
          <TabsContent value="sms" className="space-y-4">
            <Header m={sms} />
            <p className="text-sm text-muted-foreground">{t("models.sms_verdict", { scam: sms.verdict.thresholds.scam, suspicious: sms.verdict.thresholds.suspicious })}</p>
            <SplitTiles s={sms.verdict.test} />
            <CompareTable models={sms.models} deployed={sms.deployed} />
            <div className="grid gap-4 lg:grid-cols-2">
              <HBar
                title={t("models.sms_slices")}
                valueLabel="F1"
                data={Object.entries(sms.slices as Record<string, { model_plus_rules?: Split }>)
                  .filter(([, v]) => v.model_plus_rules)
                  .map(([k, v]) => ({ label: tx(`slice.${k}`, k), value: v.model_plus_rules!.f1 }))}
              />
              {cmp && (
                <div className="surface space-y-3 p-5">
                  <h2 className="font-display text-base font-semibold">{t("models.transformer")}</h2>
                  <CompareTable models={cmp.models} deployed="TF-IDF + LR (deployed)" />
                  <p className="text-sm text-muted-foreground">{cmp.decision}</p>
                </div>
              )}
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <Tile label={t("models.typing")} value={pct(sms.scam_type_classifier.pipeline_rules_then_classifier.accuracy_when_typed)} hint={t("models.typing_hint")} />
              <Tile label={t("models.typing_clf")} value={pct(sms.scam_type_classifier.accuracy)} hint={t("models.typing_clf_hint")} />
              <Tile label={t("models.test_messages")} value={String(sms.dataset.rows.test)} />
            </div>
            <Plots urls={sms.plot_urls ?? []} onOpen={setOpen} />
          </TabsContent>
        )}

        {profile && (
          <TabsContent value="data" className="space-y-4">
            <div className="surface space-y-3 p-5">
              <h2 className="font-display text-base font-semibold">{t("models.upi2024")}</h2>
              <div className="grid gap-2 sm:grid-cols-3">
                <Tile label={t("models.base_rate_plain")} value={formatPercent(profile.dataset.fraud_rate, 2)} />
                <Tile label="PR-AUC · LR" value={profile.label_check.logistic_regression.pr_auc.toFixed(4)} />
                <Tile label="PR-AUC · XGBoost" value={profile.label_check.xgboost.pr_auc.toFixed(4)} />
              </div>
              <p className="text-sm text-muted-foreground">{profile.label_check.conclusion}</p>
            </div>
            <Plots urls={profile.plot_urls ?? []} onOpen={setOpen} />
          </TabsContent>
        )}
      </Tabs>

      <Dialog open={!!open} onOpenChange={(v) => !v && setOpen(null)}>
        <DialogContent className="max-w-3xl">
          <DialogTitle className="sr-only">{t("models.plots")}</DialogTitle>
          {open && <img src={open} alt="" className="w-full rounded-lg bg-white" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}

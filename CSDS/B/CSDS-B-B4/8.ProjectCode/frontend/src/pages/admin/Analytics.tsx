import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Activity, Ban, Clock3, Flag, MessageSquareWarning, ShieldCheck, ShieldX, Wallet } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { ChartCard, ChartTooltip, axisProps } from "@/components/charts/ChartCard";
import { HBar } from "@/components/charts/HBar";
import { CardSkeleton, EmptyState, ErrorState, PageHeader } from "@/components/common/States";
import { LevelBadge, StatusBadge, pick } from "@/components/risk/RiskBits";
import { api, apiError } from "@/lib/api";
import { formatCompact, formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { Lang3, Level, Party } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Overview {
  days: number;
  payments_scored: number;
  levels: Record<Level, number>;
  held_now: number;
  holds_total: number;
  holds_released: number;
  payments_stopped: number;
  blocked: number;
  money_protected: number;
  average_score: number;
  intent_checks: number;
  intent_escalations: number;
  sms_checks: number;
  sms_scams: number;
  reports: number;
  users: number;
}
interface Flagged {
  id: number;
  reference: string;
  created_at: string;
  payer: Party;
  payee: Party;
  amount: number;
  channel: string;
  status: string;
  status_reason: string | null;
  score: number;
  level: Level;
  hold_status: string | null;
  scam_type: string | null;
  top_reasons: Lang3[];
}

function Kpi({ icon: Icon, label, value, tone }: { icon: typeof Activity; label: string; value: string; tone?: "safe" | "danger" | "caution" }) {
  return (
    <motion.div whileHover={{ y: -2 }} className="surface p-4">
      <p className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className={cn("h-4 w-4", tone === "safe" ? "text-safe" : tone === "danger" ? "text-danger" : tone === "caution" ? "text-caution" : "text-primary")} />
        {label}
      </p>
      <p className="mt-2 font-display text-2xl font-semibold tabular">{value}</p>
    </motion.div>
  );
}

function PolicyEditor() {
  const { t, tx } = useI18n();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin", "policy"], queryFn: async () => (await api.get<{ medium: number; high: number; block_report_score: number; defaults: { medium: number; high: number; block_report_score: number } }>("/admin/policy")).data });
  const [range, setRange] = useState<[number, number]>([35, 70]);
  const [block, setBlock] = useState(2.5);
  useEffect(() => {
    if (q.data) {
      setRange([q.data.medium, q.data.high]);
      setBlock(q.data.block_report_score);
    }
  }, [q.data]);
  const save = useMutation({
    mutationFn: async (v: { medium: number; high: number; block_report_score: number }) => (await api.put("/admin/policy", v)).data,
    onSuccess: () => {
      toast.success(t("admin.policy_saved"));
      qc.invalidateQueries({ queryKey: ["admin", "policy"] });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  if (!q.data) return <CardSkeleton rows={3} />;
  return (
    <section className="surface p-5">
      <h2 className="font-display text-base font-semibold">{t("admin.policy")}</h2>
      <p className="mt-1 text-sm text-muted-foreground">{t("admin.policy_hint", { medium: q.data.defaults.medium, high: q.data.defaults.high })}</p>
      <div className="mt-5 space-y-6">
        <div>
          <div className="mb-3 flex justify-between text-sm">
            <span>
              <LevelBadge level="medium" /> ≥ <b className="tabular">{range[0]}</b>
            </span>
            <span>
              <LevelBadge level="high" /> ≥ <b className="tabular">{range[1]}</b>
            </span>
          </div>
          <Slider min={5} max={99} step={1} value={range} onValueChange={(v) => setRange([Math.min(v[0], v[1] - 1), Math.max(v[1], v[0] + 1)] as [number, number])} aria-label={t("admin.policy")} />
        </div>
        <div>
          <p className="mb-3 text-sm">{t("admin.block_threshold", { value: block.toFixed(1) })}</p>
          <Slider min={0.5} max={10} step={0.5} value={[block]} onValueChange={(v) => setBlock(v[0])} aria-label={t("admin.block_label")} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => save.mutate({ medium: range[0], high: range[1], block_report_score: block })} disabled={save.isPending}>
            {t("common.save")}
          </Button>
          <Button variant="outline" onClick={() => save.mutate(q.data.defaults)} disabled={save.isPending}>
            {t("admin.policy_reset")}
          </Button>
        </div>
      </div>
    </section>
  );
}

export default function Analytics() {
  const { t, tx, lang } = useI18n();
  const [days, setDays] = useState(30);
  const overview = useQuery({ queryKey: ["admin", "overview", days], queryFn: async () => (await api.get<Overview>("/admin/overview", { params: { days } })).data });
  const trends = useQuery({ queryKey: ["admin", "trends", days], queryFn: async () => (await api.get<{ items: Record<string, number | string>[] }>("/admin/trends", { params: { days: Math.max(days, 7) } })).data });
  const types = useQuery({ queryKey: ["admin", "types", days], queryFn: async () => (await api.get<{ items: { scam_type: string; sms: number; intent: number; reports: number; total: number }[] }>("/admin/scam-types", { params: { days } })).data });
  const dist = useQuery({ queryKey: ["admin", "dist", days], queryFn: async () => (await api.get<{ histogram: { bucket: string; count: number }[]; by_hour: { hour: number; payments: number; high: number }[] }>("/admin/risk-distribution", { params: { days } })).data });
  const flagged = useQuery({ queryKey: ["admin", "flagged"], queryFn: async () => (await api.get<{ items: Flagged[] }>("/admin/flagged")).data });
  const reports = useQuery({ queryKey: ["admin", "reports"], queryFn: async () => (await api.get<{ items: { upi_id: string; name: string | null; reports: number; last_report: string; top_category: string | null; trust: number | null }[] }>("/admin/reports")).data });

  const o = overview.data;
  const series = [
    { key: "scored", label: t("admin.series.scored"), color: "var(--series-1)" },
    { key: "high", label: t("admin.series.high"), color: "var(--series-2)" },
    { key: "stopped", label: t("admin.series.stopped"), color: "var(--series-3)" },
    { key: "medium", label: t("admin.series.medium"), color: "var(--series-4)" },
  ];

  return (
    <div className="space-y-5">
      <PageHeader
        title={t("nav.admin")}
        subtitle={t("admin.subtitle")}
        actions={
          <div className="flex rounded-full border p-0.5" role="group" aria-label={t("admin.range")}>
            {[7, 30, 90].map((d) => (
              <button key={d} onClick={() => setDays(d)} className={cn("rounded-full px-3 py-1 text-sm", days === d ? "bg-primary text-primary-foreground" : "text-muted-foreground")} aria-pressed={days === d}>
                {t("admin.days", { n: d })}
              </button>
            ))}
          </div>
        }
      />

      {overview.isError ? (
        <ErrorState error={overview.error} onRetry={() => overview.refetch()} />
      ) : !o ? (
        <CardSkeleton rows={3} />
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Kpi icon={Activity} label={t("admin.kpi.scored")} value={formatCompact(o.payments_scored)} />
          <Kpi icon={ShieldX} label={t("admin.kpi.stopped")} value={String(o.payments_stopped)} tone="safe" />
          <Kpi icon={Wallet} label={t("admin.kpi.protected")} value={formatINR(o.money_protected, true)} tone="safe" />
          <Kpi icon={Clock3} label={t("admin.kpi.held_now")} value={`${o.held_now} / ${o.holds_total}`} tone="caution" />
          <Kpi icon={Ban} label={t("admin.kpi.blocked")} value={String(o.blocked)} tone="danger" />
          <Kpi icon={ShieldCheck} label={t("admin.kpi.intent")} value={`${o.intent_escalations} / ${o.intent_checks}`} />
          <Kpi icon={MessageSquareWarning} label={t("admin.kpi.sms")} value={`${o.sms_scams} / ${o.sms_checks}`} tone="danger" />
          <Kpi icon={Flag} label={t("admin.kpi.reports")} value={String(o.reports)} />
        </div>
      )}

      {trends.data && (
        <ChartCard
          title={t("admin.trends")}
          subtitle={t("admin.trends_sub")}
          legend={series.map((s) => ({ label: s.label, color: s.color }))}
          table={{ columns: [t("chart.date"), ...series.map((s) => s.label)], rows: trends.data.items.map((r) => [String(r.date), ...series.map((s) => Number(r[s.key]))]) }}
        >
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends.data.items} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                <XAxis dataKey="date" {...axisProps} tickFormatter={(d: string) => d.slice(5)} minTickGap={20} />
                <YAxis {...axisProps} allowDecimals={false} width={40} />
                <Tooltip content={<ChartTooltip />} cursor={{ stroke: "var(--chart-axis)" }} />
                {series.map((s) => (
                  <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2} dot={false} activeDot={{ r: 4, stroke: "hsl(var(--card))", strokeWidth: 2 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {dist.data && (
          <ChartCard title={t("admin.distribution")} subtitle={t("admin.distribution_sub")} table={{ columns: [t("risk.score"), t("chart.payments")], rows: dist.data.histogram.map((h) => [h.bucket, h.count]) }}>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dist.data.histogram} margin={{ top: 8, right: 8, left: -16, bottom: 0 }} barCategoryGap={2}>
                  <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                  <XAxis dataKey="bucket" {...axisProps} />
                  <YAxis {...axisProps} allowDecimals={false} width={40} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} />
                  <Bar dataKey="count" name={t("chart.payments")} radius={[4, 4, 0, 0]}>
                    {dist.data.histogram.map((h, i) => (
                      <Cell key={h.bucket} fill={i >= 7 ? "var(--status-critical)" : i >= 3 ? "var(--status-warning)" : "var(--status-good)"} />
                    ))}
                    <LabelList dataKey="count" position="top" style={{ fill: "var(--chart-ink)", fontSize: 10 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">{t("admin.distribution_note")}</p>
          </ChartCard>
        )}
        {dist.data && (
          <ChartCard title={t("admin.by_hour")} subtitle={t("admin.by_hour_sub")} table={{ columns: [t("admin.hour"), t("admin.series.high")], rows: dist.data.by_hour.map((h) => [`${String(h.hour).padStart(2, "0")}:00`, h.high]) }}>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dist.data.by_hour} margin={{ top: 8, right: 8, left: -16, bottom: 0 }} barCategoryGap={2}>
                  <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                  <XAxis dataKey="hour" {...axisProps} tickFormatter={(h: number) => String(h).padStart(2, "0")} interval={2} />
                  <YAxis {...axisProps} allowDecimals={false} width={40} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "hsl(var(--muted) / 0.6)" }} labelFormatter={(h) => `${h}:00`} />
                  <Bar dataKey="high" name={t("admin.series.high")} fill="var(--series-2)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        )}
      </div>

      {types.data && (
        <HBar
          title={t("admin.scam_types")}
          subtitle={t("admin.scam_types_sub")}
          valueLabel={t("admin.signals")}
          format={(v) => String(v)}
          labelWidth={170}
          data={types.data.items.map((i) => ({ label: tx(`scam.${i.scam_type}`, i.scam_type), value: i.total }))}
        />
      )}

      <section className="surface p-5">
        <h2 className="mb-3 font-display text-base font-semibold">{t("admin.flagged")}</h2>
        {flagged.data?.items.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead className="text-left text-xs text-muted-foreground">
                <tr>
                  <th className="py-2 font-medium">{t("admin.col.when")}</th>
                  <th className="py-2 font-medium">{t("admin.col.from_to")}</th>
                  <th className="py-2 text-right font-medium">{t("chart.amount")}</th>
                  <th className="py-2 font-medium">{t("risk.level")}</th>
                  <th className="py-2 font-medium">{t("admin.col.outcome")}</th>
                  <th className="py-2 font-medium">{t("admin.col.reason")}</th>
                </tr>
              </thead>
              <tbody>
                {flagged.data.items.map((f) => (
                  <tr key={f.id} className="border-t align-top">
                    <td className="py-2 pr-3 text-xs text-muted-foreground">{formatDateTime(f.created_at, lang)}</td>
                    <td className="py-2 pr-3">
                      <p className="font-medium">{f.payer.name}</p>
                      <p className="text-xs text-muted-foreground">→ {f.payee.name} · {f.payee.upi_id}</p>
                    </td>
                    <td className="py-2 pr-3 text-right tabular">{formatINR(f.amount)}</td>
                    <td className="py-2 pr-3">
                      <LevelBadge level={f.level} blocked={f.status === "blocked"} /> <span className="text-xs tabular text-muted-foreground">{f.score}</span>
                    </td>
                    <td className="py-2 pr-3">
                      <StatusBadge status={f.status} />
                      {f.status_reason && <p className="text-xs text-muted-foreground">{tx(`reason.${f.status_reason}`, "")}</p>}
                    </td>
                    <td className="max-w-xs py-2 text-xs text-muted-foreground">{f.top_reasons[0] ? pick(f.top_reasons[0], lang) : "–"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title={t("admin.none_flagged")} />
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <section className="surface p-5">
          <h2 className="mb-3 font-display text-base font-semibold">{t("admin.reported")}</h2>
          {reports.data?.items.length ? (
            <ul className="divide-y">
              {reports.data.items.map((r) => (
                <li key={r.upi_id} className="flex items-center gap-3 py-2.5">
                  <Flag className="h-4 w-4 shrink-0 text-danger" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-sm">{r.upi_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {r.name ?? t("admin.outside_sandbox")} · {r.top_category ? tx(`scam.${r.top_category}`, r.top_category) : ""}
                    </p>
                  </div>
                  <span className="text-right text-sm">
                    <b className="tabular">{r.reports}</b> <span className="text-xs text-muted-foreground">{t("admin.reports_word")}</span>
                    {r.trust !== null && <span className="block text-xs text-muted-foreground">{t("trust.label")} {r.trust}</span>}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title={t("admin.none_reported")} />
          )}
        </section>
        <PolicyEditor />
      </div>
    </div>
  );
}

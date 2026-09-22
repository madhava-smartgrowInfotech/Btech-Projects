import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ArrowDownLeft, ArrowUpRight, Bell, Clock3, Copy, MessageSquareWarning, QrCode, Send, ShieldCheck, ShieldX, Wallet } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { ChartCard, ChartTooltip, axisProps } from "@/components/charts/ChartCard";
import { CardSkeleton, EmptyState, ErrorState, ListSkeleton } from "@/components/common/States";
import { LEVEL_STYLE, LevelBadge, PartyRow, StatusBadge } from "@/components/risk/RiskBits";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatCompact, formatCountdown, formatDateTime, formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import type { CollectItem, Level, Payment, WalletInfo } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useNow } from "@/lib/useNow";

function Kpi({ icon: Icon, label, value, hint, tone = "default", delay = 0 }: { icon: typeof Wallet; label: string; value: string; hint?: string; tone?: "default" | "safe" | "caution"; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -2 }}
      className="surface p-4"
    >
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Icon className={cn("h-4 w-4", tone === "safe" ? "text-safe" : tone === "caution" ? "text-caution" : "text-primary")} />
        {label}
      </div>
      <p className="mt-2 font-display text-2xl font-semibold tabular">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </motion.div>
  );
}

export default function Home() {
  const { user } = useAuth();
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [qrOpen, setQrOpen] = useState(false);
  const now = useNow(1000);
  const wallet = useQuery({ queryKey: ["wallet"], queryFn: async () => (await api.get<WalletInfo>("/wallet")).data });
  const incoming = useQuery({ queryKey: ["collect", "incoming"], queryFn: async () => (await api.get<{ items: CollectItem[] }>("/collect/incoming")).data });
  const holds = useQuery({ queryKey: ["holds"], queryFn: async () => (await api.get<{ items: Payment[] }>("/holds")).data });
  const recent = useQuery({ queryKey: ["payments", "recent"], queryFn: async () => (await api.get<{ items: Payment[] }>("/payments", { params: { limit: 6 } })).data });

  const pending = incoming.data?.items.filter((i) => i.status === "pending") ?? [];
  const active = holds.data?.items.filter((p) => p.status === "held") ?? [];
  const w = wallet.data;
  const firstName = user?.full_name.split(" ")[0] ?? "";
  const hour = new Date().getHours();
  const greet = hour < 12 ? t("home.greet.morning") : hour < 17 ? t("home.greet.afternoon") : t("home.greet.evening");

  const actions = [
    { to: "/app/send", icon: Send, label: t("nav.send") },
    { to: "/app/scan", icon: QrCode, label: t("nav.scan") },
    { to: "/app/collect", icon: Bell, label: t("nav.collect"), badge: pending.length },
    { to: "/app/sms", icon: MessageSquareWarning, label: t("nav.sms") },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">{greet},</p>
          <h1 className="page-title">{firstName}</h1>
        </div>
        <GuideButton screen="home" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        {/* Balance card */}
        {wallet.isLoading ? (
          <Skeleton className="h-48 rounded-2xl" />
        ) : wallet.isError ? (
          <ErrorState error={wallet.error} onRetry={() => wallet.refetch()} />
        ) : (
          w && (
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-brand-700 via-brand-800 to-[#062a2a] p-5 text-white shadow-lift sm:p-6"
            >
              <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-teal-300/20 blur-3xl" />
              <div className="pointer-events-none absolute -bottom-24 left-10 h-48 w-48 rounded-full bg-amber-400/15 blur-3xl" />
              <div className="relative flex items-start justify-between">
                <div>
                  <p className="text-sm text-white/70">{t("home.balance")}</p>
                  <p className="mt-1 font-display text-4xl font-semibold tabular sm:text-5xl">{formatINR(w.balance)}</p>
                </div>
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-medium text-amber-200">{t("common.sandbox_short")}</span>
              </div>
              <div className="relative mt-6 flex flex-wrap items-center gap-2">
                <button
                  className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-sm transition hover:bg-white/15"
                  onClick={() => {
                    navigator.clipboard?.writeText(w.upi_id).then(() => toast.success(t("common.copied")));
                  }}
                >
                  <span className="font-mono">{w.upi_id}</span>
                  <Copy className="h-3.5 w-3.5 opacity-80" />
                </button>
                <Button size="sm" variant="secondary" className="bg-white text-brand-900 hover:bg-white/90" onClick={() => setQrOpen(true)}>
                  <QrCode className="mr-1.5 h-4 w-4" />
                  {t("home.my_qr")}
                </Button>
              </div>
              <div className="relative mt-5 grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-white/80">
                  <ArrowUpRight className="h-4 w-4 text-rose-200" />
                  {t("home.spent_month")} <span className="font-semibold text-white tabular">{formatINR(w.stats.spent_this_month, true)}</span>
                </div>
                <div className="flex items-center gap-2 text-white/80">
                  <ArrowDownLeft className="h-4 w-4 text-emerald-200" />
                  {t("home.received_month")} <span className="font-semibold text-white tabular">{formatINR(w.stats.received_this_month, true)}</span>
                </div>
              </div>
            </motion.div>
          )
        )}

        {/* Quick actions */}
        <div className="grid grid-cols-2 gap-3">
          {actions.map((a, i) => (
            <motion.div key={a.to} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 * i }} whileTap={{ scale: 0.97 }}>
              <Link to={a.to} className="surface group relative flex h-full flex-col justify-between gap-6 p-4 transition hover:border-primary/40 hover:shadow-lift">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary transition group-hover:bg-primary group-hover:text-primary-foreground">
                  <a.icon className="h-5 w-5" />
                </span>
                <span className="font-medium">{a.label}</span>
                {!!a.badge && <span className="absolute right-3 top-3 grid h-6 min-w-6 place-items-center rounded-full bg-danger px-1.5 text-xs font-bold text-danger-foreground">{a.badge}</span>}
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Waiting for you: collect requests and holds */}
      {(pending.length > 0 || active.length > 0) && (
        <div className="grid gap-3 md:grid-cols-2">
          {pending.slice(0, 2).map((r) => (
            <Link key={r.id} to="/app/collect" className="surface flex items-center gap-3 border-caution/40 p-4 transition hover:shadow-lift">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-caution-soft text-caution">
                <Bell className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{t("home.request_from", { name: r.counterparty.name })}</p>
                <p className="text-xs text-danger">{t("collect.debit_short", { amount: formatINR(r.amount) })}</p>
              </div>
              <span className="font-semibold tabular">{formatINR(r.amount)}</span>
            </Link>
          ))}
          {active.slice(0, 2).map((p) => (
            <Link key={p.id} to={`/app/pay/${p.id}`} className="surface flex items-center gap-3 border-caution/40 p-4 transition hover:shadow-lift">
              <span className="grid h-10 w-10 place-items-center rounded-full bg-caution-soft text-caution">
                <Clock3 className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{t("home.on_hold_to", { name: p.counterparty.name })}</p>
                <p className="text-xs text-muted-foreground">
                  {t("hold.releases_in")} {p.hold ? formatCountdown(new Date(p.hold.hold_until).getTime() - now) : ""}
                </p>
              </div>
              <span className="font-semibold tabular">{formatINR(p.amount)}</span>
            </Link>
          ))}
        </div>
      )}

      {/* KPIs */}
      {w ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi icon={ShieldCheck} label={t("home.kpi.checked")} value={formatCompact(w.stats.payments_checked)} hint={t("home.kpi.checked_hint")} />
          <Kpi icon={ShieldX} label={t("home.kpi.stopped")} value={String(w.stats.payments_stopped)} hint={t("home.kpi.stopped_hint")} tone="safe" delay={0.05} />
          <Kpi icon={Wallet} label={t("home.kpi.protected")} value={formatINR(w.stats.money_protected, true)} hint={t("home.kpi.protected_hint")} tone="safe" delay={0.1} />
          <Kpi icon={Clock3} label={t("home.kpi.on_hold")} value={String(w.stats.on_hold)} hint={t("home.kpi.on_hold_hint")} tone="caution" delay={0.15} />
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      )}

      {/* Charts */}
      {w && (
        <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
          <ChartCard
            title={t("home.chart.spend")}
            subtitle={t("home.chart.spend_sub")}
            table={{ columns: [t("chart.date"), t("chart.amount")], rows: w.daily_spend.map((d) => [d.date, formatINR(d.amount)]) }}
          >
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={w.daily_spend} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <defs>
                    <linearGradient id="spendFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--series-1)" stopOpacity={0.28} />
                      <stop offset="100%" stopColor="var(--series-1)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
                  <XAxis dataKey="date" {...axisProps} tickFormatter={(d: string) => d.slice(8)} interval="preserveStartEnd" minTickGap={16} />
                  <YAxis {...axisProps} width={48} tickFormatter={(v: number) => formatCompact(v)} />
                  <Tooltip content={<ChartTooltip format={(v) => formatINR(v)} />} cursor={{ stroke: "var(--chart-axis)" }} />
                  <Area type="monotone" dataKey="amount" name={t("chart.amount")} stroke="var(--series-1)" strokeWidth={2} fill="url(#spendFill)" activeDot={{ r: 5, strokeWidth: 2, stroke: "hsl(var(--card))" }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
          <ChartCard
            title={t("home.chart.risk")}
            subtitle={t("home.chart.risk_sub")}
            table={{ columns: [t("risk.level"), t("chart.payments")], rows: (["low", "medium", "high"] as Level[]).map((l) => [t(LEVEL_STYLE[l].key), w.stats.levels_30d[l]]) }}
          >
            <RiskMix levels={w.stats.levels_30d} />
          </ChartCard>
        </div>
      )}

      {/* Recent activity */}
      <section className="surface p-4 sm:p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-base font-semibold">{t("home.recent")}</h2>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/app/history">{t("common.view_all")}</Link>
          </Button>
        </div>
        {recent.isLoading ? (
          <ListSkeleton rows={4} />
        ) : recent.isError ? (
          <ErrorState error={recent.error} onRetry={() => recent.refetch()} />
        ) : recent.data?.items.length ? (
          <ul className="divide-y">
            {recent.data.items.map((p) => (
              <li key={p.id}>
                <button className="flex w-full items-center gap-3 py-3 text-left" onClick={() => navigate(`/app/history/${p.id}`)}>
                  <PartyRow
                    party={p.counterparty}
                    sub={<span className="flex items-center gap-2">{formatDateTime(p.created_at, lang)} <StatusBadge status={p.status} /></span>}
                    right={
                      <div className="flex flex-col items-end gap-1">
                        <span className={cn("font-semibold tabular", p.direction === "received" ? "text-safe" : "")}>
                          {p.direction === "received" ? "+" : "−"}
                          {formatINR(p.amount)}
                        </span>
                        {p.direction === "sent" && p.level && p.level !== "low" && <LevelBadge level={p.level} />}
                      </div>
                    }
                    className="flex-1"
                  />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title={t("home.no_activity")} description={t("home.no_activity_hint")} action={<Button asChild><Link to="/app/send">{t("nav.send")}</Link></Button>} />
        )}
      </section>

      <Dialog open={qrOpen} onOpenChange={setQrOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t("home.my_qr")}</DialogTitle>
            <DialogDescription>{t("home.my_qr_hint")}</DialogDescription>
          </DialogHeader>
          {w ? (
            <div className="flex flex-col items-center gap-3">
              <img src={`/api/wallet/qr.png?t=${w.upi_id}`} alt={t("home.my_qr")} className="h-56 w-56 rounded-xl border bg-white p-2" />
              <p className="font-mono text-sm">{w.upi_id}</p>
            </div>
          ) : (
            <CardSkeleton />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RiskMix({ levels }: { levels: Record<Level, number> }) {
  const { t } = useI18n();
  const total = Math.max(1, levels.low + levels.medium + levels.high);
  return (
    <ul className="space-y-4 pt-2">
      {(["low", "medium", "high"] as Level[]).map((l, i) => {
        const s = LEVEL_STYLE[l];
        const share = levels[l] / total;
        return (
          <li key={l}>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className={cn("flex items-center gap-1.5 font-medium", s.cls)}>
                <s.icon className="h-4 w-4" />
                {t(s.key)}
              </span>
              <span className="tabular text-muted-foreground">
                {levels[l]} · {Math.round(share * 100)}%
              </span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-muted">
              <motion.div className="h-full rounded-full" style={{ background: s.color }} initial={{ width: 0 }} animate={{ width: `${Math.max(share * 100, levels[l] ? 2 : 0)}%` }} transition={{ delay: 0.1 * i, duration: 0.6 }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}

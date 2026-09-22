import { useEffect } from "react";
import { motion, useReducedMotion, useSpring, useTransform } from "motion/react";
import { AlertTriangle, Ban, BadgeCheck, CheckCircle2, CircleAlert, Clock3, ShieldAlert, ShieldCheck, ShieldQuestion, Store, XCircle } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useI18n } from "@/lib/i18n";
import { initials } from "@/lib/format";
import type { Lang3, Level, Party, PaymentStatus, Reason, Trust } from "@/lib/types";
import { cn } from "@/lib/utils";
import type { MessageKey } from "@/locales/en";

export function pick(text: Lang3 | null | undefined, lang: string): string {
  if (!text) return "";
  return (text as Record<string, string>)[lang] ?? text.en;
}

export const LEVEL_STYLE: Record<Level | "blocked", { icon: typeof ShieldCheck; cls: string; soft: string; key: MessageKey; color: string }> = {
  low: { icon: ShieldCheck, cls: "text-safe", soft: "bg-safe-soft text-safe border-safe/30", key: "risk.level.low", color: "var(--status-good)" },
  medium: { icon: AlertTriangle, cls: "text-caution", soft: "bg-caution-soft text-caution border-caution/30", key: "risk.level.medium", color: "var(--status-warning)" },
  high: { icon: ShieldAlert, cls: "text-danger", soft: "bg-danger-soft text-danger border-danger/30", key: "risk.level.high", color: "var(--status-critical)" },
  blocked: { icon: Ban, cls: "text-danger", soft: "bg-danger text-danger-foreground border-danger", key: "risk.level.blocked", color: "var(--status-critical)" },
};

export function LevelBadge({ level, blocked = false, className }: { level: Level | null | undefined; blocked?: boolean; className?: string }) {
  const { t } = useI18n();
  if (!level) return null;
  const s = LEVEL_STYLE[blocked ? "blocked" : level];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold", s.soft, className)}>
      <s.icon className="h-3.5 w-3.5" />
      {t(s.key)}
    </span>
  );
}

const STATUS: Record<string, { icon: typeof CheckCircle2; cls: string }> = {
  completed: { icon: CheckCircle2, cls: "text-safe" },
  held: { icon: Clock3, cls: "text-caution" },
  cancelled: { icon: XCircle, cls: "text-muted-foreground" },
  rejected: { icon: XCircle, cls: "text-danger" },
  blocked: { icon: Ban, cls: "text-danger" },
  draft: { icon: CircleAlert, cls: "text-muted-foreground" },
  declined: { icon: XCircle, cls: "text-muted-foreground" },
  failed: { icon: XCircle, cls: "text-danger" },
};

export function StatusBadge({ status, className }: { status: PaymentStatus | string; className?: string }) {
  const { tx } = useI18n();
  const s = STATUS[status] ?? STATUS.draft;
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs font-medium", s.cls, className)}>
      <s.icon className="h-3.5 w-3.5" />
      {tx(`status.${status}`, status)}
    </span>
  );
}

/** Half-circle gauge: 0-100 with the policy bands; the needle springs into place. */
export function RiskGauge({ score, level, medium = 35, high = 70, size = 220 }: { score: number; level: Level; medium?: number; high?: number; size?: number }) {
  const { t } = useI18n();
  const reduce = useReducedMotion();
  const r = 80;
  const cx = 100;
  const cy = 96;
  const needle = r - 20;
  const value = useSpring(reduce ? score : 0, { stiffness: 70, damping: 14 });
  useEffect(() => {
    value.set(Math.max(0, Math.min(100, score)));
  }, [score, value]);
  const x2 = useTransform(value, (v) => cx + needle * Math.cos(Math.PI * (1 - v / 100)));
  const y2 = useTransform(value, (v) => cy - needle * Math.sin(Math.PI * (1 - v / 100)));
  const arc = (from: number, to: number) => {
    const a0 = Math.PI * (1 - from / 100);
    const a1 = Math.PI * (1 - to / 100);
    return `M ${cx + r * Math.cos(a0)} ${cy - r * Math.sin(a0)} A ${r} ${r} 0 0 1 ${cx + r * Math.cos(a1)} ${cy - r * Math.sin(a1)}`;
  };
  const s = LEVEL_STYLE[level];
  return (
    <div className="relative mx-auto" style={{ width: size, maxWidth: "100%" }} role="img" aria-label={`${t("risk.score")} ${score} / 100, ${t(s.key)}`}>
      <svg viewBox="0 0 200 106" className="w-full">
        <path d={arc(0, 100)} fill="none" stroke="hsl(var(--muted))" strokeWidth="14" strokeLinecap="round" />
        <path d={arc(0.5, medium - 0.8)} fill="none" stroke="var(--status-good)" strokeWidth="14" strokeLinecap="round" opacity={level === "low" ? 1 : 0.35} />
        <path d={arc(medium + 0.8, high - 0.8)} fill="none" stroke="var(--status-warning)" strokeWidth="14" opacity={level === "medium" ? 1 : 0.35} />
        <path d={arc(high + 0.8, 99.5)} fill="none" stroke="var(--status-critical)" strokeWidth="14" strokeLinecap="round" opacity={level === "high" ? 1 : 0.35} />
        <motion.line x1={cx} y1={cy} x2={x2} y2={y2} stroke="hsl(var(--foreground))" strokeWidth="4" strokeLinecap="round" />
        <circle cx={cx} cy={cy} r="7" fill="hsl(var(--foreground))" />
        <circle cx={cx} cy={cy} r="3" fill="hsl(var(--card))" />
      </svg>
      <div className="mt-1 text-center">
        <div className="font-display text-4xl font-semibold leading-none tabular">{score}</div>
        <div className={cn("mt-1.5 inline-flex items-center gap-1 text-sm font-semibold", s.cls)}>
          <s.icon className="h-4 w-4" />
          {t(s.key)}
        </div>
      </div>
    </div>
  );
}

export function TrustBadge({ trust, className }: { trust: Trust | null | undefined; className?: string }) {
  const { t, tx } = useI18n();
  if (!trust) return null;
  const Icon = trust.band === "trusted" ? BadgeCheck : trust.band === "caution" ? ShieldQuestion : ShieldAlert;
  const cls = trust.band === "trusted" ? "text-safe bg-safe-soft border-safe/30" : trust.band === "caution" ? "text-caution bg-caution-soft border-caution/30" : "text-danger bg-danger-soft border-danger/30";
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold", cls, className)}>
          <Icon className="h-3.5 w-3.5" />
          {t("trust.label")} {trust.score}
          <span className="font-normal opacity-80">· {tx(`trust.band.${trust.band}`)}</span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72" align="start">
        <p className="text-sm font-semibold">{t("trust.title")}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{t("trust.explain")}</p>
        <ul className="mt-3 space-y-1.5 text-sm">
          <li className="flex justify-between">
            <span className="text-muted-foreground">{t("trust.start")}</span>
            <span className="tabular">60</span>
          </li>
          {trust.components.map((c) => (
            <li key={c.code} className="flex justify-between gap-3">
              <span>{tx(`trust.part.${c.code}`, c.code)}</span>
              <span className={cn("tabular font-medium", c.delta < 0 ? "text-danger" : "text-safe")}>
                {c.delta > 0 ? "+" : ""}
                {c.delta}
              </span>
            </li>
          ))}
          <li className="flex justify-between border-t pt-1.5 font-semibold">
            <span>{t("trust.total")}</span>
            <span className="tabular">{trust.score}</span>
          </li>
        </ul>
        <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <dt>{t("trust.account_age")}</dt>
          <dd className="text-right tabular">{t("trust.days", { n: trust.account_age_days })}</dd>
          <dt>{t("trust.reports")}</dt>
          <dd className="text-right tabular">{trust.report_count}</dd>
          <dt>{t("trust.payers_7d")}</dt>
          <dd className="text-right tabular">{trust.distinct_payers_7d}</dd>
          <dt>{t("trust.new_payer_share")}</dt>
          <dd className="text-right tabular">{Math.round(trust.new_payer_share_7d * 100)}%</dd>
        </dl>
      </PopoverContent>
    </Popover>
  );
}

export function ReasonList({ reasons, reassurance = [], className }: { reasons: Reason[]; reassurance?: Reason[]; className?: string }) {
  const { lang, t } = useI18n();
  if (!reasons.length && !reassurance.length) return <p className="text-sm text-muted-foreground">{t("risk.no_reasons")}</p>;
  return (
    <ul className={cn("space-y-2", className)}>
      {reasons.map((r, i) => (
        <motion.li
          key={`${r.code}-${i}`}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.08 * i }}
          className={cn("flex items-start gap-2.5 rounded-xl border px-3 py-2.5 text-sm", r.kind === "guard" ? "border-danger/40 bg-danger-soft" : "bg-card")}
        >
          <AlertTriangle className={cn("mt-0.5 h-4 w-4 shrink-0", r.kind === "guard" ? "text-danger" : "text-caution")} />
          <span className={cn(r.kind === "guard" && "font-medium")}>{pick(r.text, lang)}</span>
        </motion.li>
      ))}
      {reassurance.map((r, i) => (
        <li key={`${r.code}-s${i}`} className="flex items-start gap-2.5 rounded-xl border border-dashed px-3 py-2 text-sm text-muted-foreground">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-safe" />
          <span>{pick(r.text, lang)}</span>
        </li>
      ))}
    </ul>
  );
}

/** SHAP contributions as diverging bars: right = pushes risk up, left = lowers it. */
export function ContributionBars({ items, max = 8 }: { items: { feature: string; value: number }[]; max?: number }) {
  const { tx, t } = useI18n();
  const rows = items.slice(0, max);
  const peak = Math.max(0.01, ...rows.map((r) => Math.abs(r.value)));
  return (
    <div>
      <div className="mb-2 flex justify-between text-2xs text-muted-foreground">
        <span>← {t("risk.lowers")}</span>
        <span>{t("risk.raises")} →</span>
      </div>
      <ul className="space-y-1.5" aria-label={t("risk.contributions")}>
        {rows.map((r) => {
          const w = (Math.abs(r.value) / peak) * 50;
          const positive = r.value > 0;
          return (
            <li key={r.feature} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] items-center gap-3 text-xs" title={`${r.value > 0 ? "+" : ""}${r.value.toFixed(3)}`}>
              <span className="truncate text-right text-muted-foreground">{tx(`feature.${r.feature}`, r.feature)}</span>
              <span className="relative h-3.5">
                <span className="absolute inset-y-0 left-1/2 w-px bg-border" />
                <motion.span
                  initial={{ width: 0 }}
                  animate={{ width: `${w}%` }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                  className="absolute inset-y-0 rounded-sm"
                  style={{
                    [positive ? "left" : "right"]: "50%",
                    background: positive ? "var(--status-critical)" : "var(--series-1)",
                  }}
                />
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function PartyAvatar({ party, size = "md" }: { party: Pick<Party, "name" | "is_merchant">; size?: "sm" | "md" | "lg" }) {
  const dims = size === "lg" ? "h-14 w-14 text-lg" : size === "sm" ? "h-8 w-8 text-xs" : "h-10 w-10 text-sm";
  return (
    <span
      className={cn("grid shrink-0 place-items-center rounded-full font-semibold", dims, party.is_merchant ? "text-[color:var(--series-2)]" : "text-primary")}
      style={{ background: party.is_merchant ? "color-mix(in srgb, var(--series-2) 14%, transparent)" : "hsl(var(--primary) / 0.12)" }}
    >
      {party.is_merchant ? <Store className="h-[45%] w-[45%]" /> : initials(party.name)}
    </span>
  );
}

export function PartyRow({ party, sub, right, className }: { party: Party; sub?: React.ReactNode; right?: React.ReactNode; className?: string }) {
  const { t } = useI18n();
  return (
    <div className={cn("flex min-w-0 items-center gap-3", className)}>
      <PartyAvatar party={party} />
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-1.5 truncate font-medium">
          <span className="truncate">{party.name}</span>
          {party.is_sample && <span className="shrink-0 rounded bg-muted px-1.5 py-px text-[10px] font-medium text-muted-foreground">{t("common.sample")}</span>}
        </p>
        <p className="truncate text-xs text-muted-foreground">{sub ?? party.upi_id}</p>
      </div>
      {right}
    </div>
  );
}

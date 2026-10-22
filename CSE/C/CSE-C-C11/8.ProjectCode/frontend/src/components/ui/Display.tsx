import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";

import { CountUp } from "@/components/motion/CountUp";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/utils";

/** KPI tile: animated value, optional delta and a gradient sparkline. */
export function StatCard({
  label,
  value,
  format,
  display,
  hint,
  delta,
  icon,
  spark,
  accent = "violet",
  className,
}: {
  label: string;
  /** Numeric value for CountUp; omit and pass `display` for text values. */
  value?: number | null;
  format?: (n: number) => string;
  display?: ReactNode;
  hint?: ReactNode;
  delta?: { value: string; positive?: boolean } | null;
  icon?: ReactNode;
  spark?: number[];
  accent?: "violet" | "cyan" | "magenta";
  className?: string;
}) {
  const color = accent === "cyan" ? "#22D3EE" : accent === "magenta" ? "#F472B6" : "#7C5CFF";
  const gid = `spark-${label.replace(/\W/g, "")}`;
  return (
    <Card className={cn("flex min-h-[132px] flex-col justify-between gap-3 p-5", className)}>
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm text-muted-foreground">{label}</span>
        {icon && (
          <span
            className="grid size-8 place-items-center rounded-xl text-white shadow-lg [&_svg]:size-4"
            style={{ backgroundImage: `linear-gradient(135deg, ${color}, ${accent === "cyan" ? "#7C5CFF" : "#22D3EE"})` }}
          >
            {icon}
          </span>
        )}
      </div>
      <div className="flex items-end justify-between gap-3">
        <div className="min-w-0">
          <div className="font-display text-3xl font-semibold tracking-tight tabular-nums">
            {value !== undefined && value !== null ? <CountUp value={value} format={format} /> : (display ?? "-")}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {delta && (
              <span className={cn("rounded-full px-1.5 py-0.5 font-medium", delta.positive ? "bg-success/12 text-success" : "bg-muted text-muted-foreground")}>
                {delta.value}
              </span>
            )}
            {hint}
          </div>
        </div>
        {spark && spark.length > 1 && spark.some((v) => v > 0) && (
          <div className="h-10 w-24 shrink-0" aria-hidden>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={spark.map((v, i) => ({ i, v }))} margin={{ top: 2, bottom: 2, left: 0, right: 0 }}>
                <defs>
                  <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={0.5} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#${gid})`} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
}

export function KeyValueList({
  items,
  className,
  columns = 1,
}: {
  items: { label: ReactNode; value: ReactNode; extra?: ReactNode }[];
  className?: string;
  columns?: 1 | 2;
}) {
  return (
    <dl className={cn("grid gap-x-6", columns === 2 && "sm:grid-cols-2", className)}>
      {items.map((item, i) => (
        <div key={i} className="flex flex-col gap-1 border-b border-[var(--glass-border)] py-3 last:border-0 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
          <dt className="shrink-0 text-sm text-muted-foreground">{item.label}</dt>
          <dd className="min-w-0 text-sm font-medium sm:text-right">
            <div className="tabular-nums">{item.value}</div>
            {item.extra && <div className="mt-1 flex flex-wrap gap-1 sm:justify-end">{item.extra}</div>}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function Timeline({
  items,
  className,
}: {
  items: { icon?: ReactNode; title: ReactNode; meta?: ReactNode; body?: ReactNode; trailing?: ReactNode; onClick?: () => void }[];
  className?: string;
}) {
  return (
    <ol className={cn("relative", className)}>
      {items.map((item, i) => {
        const Inner = item.onClick ? "button" : "div";
        return (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: Math.min(i, 10) * 0.04 }}
            className="relative pl-10"
          >
            {i < items.length - 1 && <span aria-hidden className="absolute left-[15px] top-9 h-[calc(100%-1.75rem)] w-px bg-gradient-to-b from-[var(--violet)]/50 to-transparent" />}
            <span className="absolute left-0 top-2 grid size-8 place-items-center rounded-full bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)] [&_svg]:size-4">
              {item.icon}
            </span>
            <Inner
              {...(item.onClick ? { type: "button" as const, onClick: item.onClick } : {})}
              className={cn("flex w-full items-start justify-between gap-3 rounded-xl px-2 py-2 text-left", item.onClick && "transition-colors hover:bg-muted")}
            >
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium">{item.title}</span>
                {item.meta && <span className="block text-xs text-muted-foreground">{item.meta}</span>}
                {item.body && <span className="mt-1 block text-sm text-muted-foreground">{item.body}</span>}
              </span>
              {item.trailing && <span className="shrink-0">{item.trailing}</span>}
            </Inner>
          </motion.li>
        );
      })}
    </ol>
  );
}

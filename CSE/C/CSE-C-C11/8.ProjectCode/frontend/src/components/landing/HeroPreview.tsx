import { Area, AreaChart, ResponsiveContainer } from "recharts";

import { HealthRing } from "@/components/charts/HealthRing";
import { LogoMark } from "@/components/brand/Logo";
import { Skeleton } from "@/components/ui/Feedback";
import { makeMoney, monthLabel } from "@/lib/format";
import { useShowcase } from "@/lib/queries";

const money = makeMoney("INR");

/** Hero card built from the demo account's real dashboard numbers. */
export function HeroPreview() {
  const { data, isPending, isError } = useShowcase();
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div aria-hidden className="absolute -inset-8 rounded-[2.5rem] bg-grad-primary opacity-25 blur-3xl" />
      <div className="glass-strong sweep relative space-y-4 rounded-3xl p-5">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <LogoMark className="size-6" />
          <span className="font-medium text-foreground">{data ? `${data.month_name} ${data.year}` : "This month"}</span>
          <span className="ml-auto rounded-full border border-[var(--glass-border)] px-2 py-0.5">Demo account · fictional data</span>
        </div>
        {isPending && (
          <div className="space-y-3" role="status" aria-label="Loading preview">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        )}
        {isError && <p className="py-10 text-center text-sm text-muted-foreground">Start the server (run.bat) to see a live preview here.</p>}
        {data && (
          <>
            <div className="flex items-center gap-4">
              <HealthRing score={data.health.score} />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Financial health</p>
                <p className="font-display text-xl font-semibold">{data.health.rating}</p>
                <p className="text-xs text-muted-foreground">Focus area: {data.health.weakest_area.replace(/_/g, " ")}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              {[
                ["Income", money.compact(data.metrics.monthly_income)],
                ["Spent", money.compact(data.metrics.monthly_expenses)],
                ["Saved", `${Math.round(data.metrics.savings_rate)}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] px-2 py-2">
                  <p className="text-[11px] text-muted-foreground">{label}</p>
                  <p className="font-display text-base font-semibold tabular-nums">{value}</p>
                </div>
              ))}
            </div>
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Spending, last {data.charts.trend.length} months</p>
              <div className="h-20" aria-hidden>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.charts.trend.map((t) => ({ m: monthLabel(t.month), v: t.expense }))} margin={{ top: 4, bottom: 0, left: 0, right: 0 }}>
                    <defs>
                      <linearGradient id="hero-area" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#7C5CFF" stopOpacity={0.55} />
                        <stop offset="100%" stopColor="#22D3EE" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="v" stroke="#7C5CFF" strokeWidth={2.5} fill="url(#hero-area)" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

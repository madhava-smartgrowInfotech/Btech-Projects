import { Gauge, PiggyBank, Receipt, Scale, Target, Wallet } from "lucide-react";
import type { ReactNode } from "react";

import { CountUp } from "@/components/motion/CountUp";
import { Reveal } from "@/components/motion/Reveal";
import { Skeleton } from "@/components/ui/Feedback";
import { makeMoney } from "@/lib/format";
import { useShowcase } from "@/lib/queries";

const money = makeMoney("INR");

/** Numbers computed live from the fictional demo account (GET /public/showcase). */
export function StatsStrip() {
  const query = useShowcase();

  if (query.isError) {
    return (
      <p className="mx-auto max-w-6xl px-4 text-center text-sm text-muted-foreground sm:px-6">
        Live demo numbers appear here once the FINJARVIS server is running (start run.bat).
      </p>
    );
  }

  const d = query.data;
  const m = d?.metrics;
  const stats: { icon: ReactNode; label: string; value: number | undefined; format: (n: number) => string }[] = [
    { icon: <Wallet />, label: "Net worth", value: m?.net_worth, format: (n) => money.compact(n) },
    { icon: <PiggyBank />, label: "Savings rate", value: m?.savings_rate, format: (n) => `${Math.round(n)}%` },
    { icon: <Gauge />, label: "Health score", value: d?.health.score, format: (n) => `${Math.round(n)}/100` },
    { icon: <Receipt />, label: "Spent this month", value: m?.monthly_expenses, format: (n) => money.compact(n) },
    { icon: <Scale />, label: "Budget used (avg.)", value: m?.avg_budget_usage, format: (n) => `${Math.round(n)}%` },
    { icon: <Target />, label: "Active goals", value: d?.counts.goals, format: (n) => String(Math.round(n)) },
  ];

  return (
    <section aria-labelledby="stats-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="glass relative overflow-hidden rounded-3xl px-5 py-8 sm:px-8">
        <div aria-hidden className="absolute -top-24 left-1/2 h-48 w-2/3 -translate-x-1/2 rounded-full bg-violet/25 blur-3xl" />
        <div className="relative mb-6 flex flex-col gap-1 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">Computed live, not mocked</p>
          <h2 id="stats-title" className="font-display text-xl font-semibold sm:text-2xl">
            What FINJARVIS shows for the demo account
          </h2>
          <p className="text-sm text-muted-foreground">
            {d ? `${d.month_name} ${d.year} · fictional transactions, budgets, goals and investments` : "Loading the demo account…"}
          </p>
        </div>
        {query.isPending ? (
          <div className="relative grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6" role="status" aria-label="Loading demo numbers">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="mx-auto h-8 w-16" />
                <Skeleton className="mx-auto h-3 w-24" />
              </div>
            ))}
          </div>
        ) : (
          <Reveal className="relative grid grid-cols-2 gap-x-4 gap-y-6 sm:grid-cols-3 lg:grid-cols-6">
            {stats.map((s) => (
              <div key={s.label} data-reveal className="flex flex-col items-center gap-1.5 text-center">
                <span className="text-violet-ink [&_svg]:size-4">{s.icon}</span>
                <span className="font-display text-2xl font-semibold sm:text-3xl">
                  <CountUp value={s.value ?? 0} format={s.format} className="text-gradient" />
                </span>
                <span className="text-xs text-muted-foreground">{s.label}</span>
              </div>
            ))}
          </Reveal>
        )}
      </div>
    </section>
  );
}

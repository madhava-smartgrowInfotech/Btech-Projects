import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, CircleDollarSign, CreditCard, Landmark, PieChart as PieIcon, PiggyBank, Plus, Receipt, Scale, Sparkles, Target, TrendingUp, Wallet } from "lucide-react";
import { Link } from "react-router";

import { ChartCard, STATUS } from "@/components/charts/Chart";
import { ColorBars, Donut, GroupedBars, TrendChart } from "@/components/charts/FinanceCharts";
import { HealthRing } from "@/components/charts/HealthRing";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { humanize, pct, useMoney } from "@/lib/format";
import { useDashboard, useRefreshData } from "@/lib/queries";
import { cn } from "@/lib/utils";

function DashboardSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading dashboard">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-[132px] rounded-2xl" />
        ))}
      </div>
      <Skeleton className="h-56 w-full rounded-2xl" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-80 rounded-2xl" />
        <Skeleton className="h-80 rounded-2xl" />
      </div>
    </div>
  );
}

const FACTOR_LABEL: Record<string, string> = {
  savings_rate: "Savings rate",
  expense_ratio: "Spending vs income",
  budget_adherence: "Budget adherence",
  emergency_fund: "Cash cushion",
  investment_diversification: "Diversification",
  goal_progress: "Goal progress",
};

export default function Dashboard() {
  const { data, isPending, isError, error, refetch } = useDashboard();
  const money = useMoney();
  const refresh = useRefreshData();
  const demo = useMutation({
    mutationFn: async () => (await api.post("/profile/demo-data")).data,
    onSuccess: async () => {
      await refresh();
      toast.success("Demo data loaded. Explore the dashboard!");
    },
    onError: (e) => toast.error(errorMessage(e)),
  });

  if (isPending) return <><PageHeader title="Dashboard" description="Loading your overview…" /><DashboardSkeleton /></>;
  if (isError) return <><PageHeader title="Dashboard" /><ErrorState error={error} title="Couldn't load your dashboard" onRetry={() => void refetch()} hint="Check that the FINJARVIS server is running." /></>;

  const { metrics: m, health, charts } = data;
  const nothingYet = charts.category_spend.length === 0 && charts.trend.length === 0 && data.counts.budgets + data.counts.goals + data.counts.holdings === 0;

  return (
    <>
      <PageHeader
        eyebrow={`${data.month_name} ${data.year}`}
        title="Dashboard"
        description="Your month at a glance: balance, spending, savings and how healthy it all looks."
        actions={
          <Button asChild>
            <Link to="/app/transactions">
              <Plus /> Add transaction
            </Link>
          </Button>
        }
      />

      {nothingYet ? (
        <EmptyState
          icon={<Wallet />}
          title="Nothing to show yet"
          description="Add your first transaction, import a statement, or load fictional demo data to see how FINJARVIS looks with a few months of history."
          action={
            <>
              <Button asChild>
                <Link to="/app/transactions">
                  <Plus /> Add a transaction
                </Link>
              </Button>
              <Button variant="secondary" loading={demo.isPending} onClick={() => demo.mutate()}>
                <Sparkles /> Load demo data
              </Button>
            </>
          }
        />
      ) : (
        <div className="space-y-6">
          <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: "Total balance", value: m.total_balance, icon: <Landmark />, accent: "violet" as const, hint: "All income minus all expenses" },
              { label: "Monthly income", value: m.monthly_income, icon: <CircleDollarSign />, accent: "cyan" as const, hint: "This month" },
              { label: "Monthly expenses", value: m.monthly_expenses, icon: <Receipt />, accent: "magenta" as const, hint: "This month" },
              { label: "Savings this month", value: m.monthly_savings, icon: <PiggyBank />, accent: "violet" as const, hint: "Income minus expenses" },
            ].map((s) => (
              <StaggerItem key={s.label}>
                <StatCard label={s.label} value={s.value} format={(n) => money(n)} icon={s.icon} accent={s.accent} hint={s.hint} />
              </StaggerItem>
            ))}
            <StaggerItem>
              <StatCard label="Savings rate" value={m.savings_rate} format={(n) => pct(n, 1)} icon={<TrendingUp />} accent="cyan" hint="Share of income kept" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Investment value" value={m.investment_value} format={(n) => money(n)} icon={<BarChart3 />} accent="magenta" hint={`${data.counts.holdings} holdings`} />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Net worth" value={m.net_worth} format={(n) => money(n)} icon={<Wallet />} accent="violet" hint="Cash position + investments" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Avg. budget usage" value={m.avg_budget_usage} format={(n) => `${Math.round(n)}%`} icon={<Scale />} accent="cyan" hint={`${data.counts.budgets} budgets this month`} />
            </StaggerItem>
          </Stagger>

          <Card>
            <CardHeader title="Financial health score" description="Six weighted factors, all calculated from your own data" icon={<Target />} />
            <CardBody className="grid gap-6 lg:grid-cols-[auto_1fr_1.2fr] lg:items-center">
              <div className="flex items-center gap-4">
                <HealthRing score={health.score} size="size-32" />
                <div>
                  <p className="font-display text-xl font-semibold">{health.rating}</p>
                  <p className="text-sm text-muted-foreground">out of 100</p>
                </div>
              </div>
              <div className="space-y-2">
                <p>{health.explanation}</p>
                <p className="text-sm text-muted-foreground">
                  Area to focus on: <strong className="text-foreground">{humanize(health.weakest_area)}</strong> — {health.weakest_area_reason}.
                </p>
              </div>
              <ul className="space-y-2.5" aria-label="Score breakdown">
                {Object.entries(health.components).map(([k, v]) => (
                  <li key={k} className="grid grid-cols-[8.5rem_1fr_2.5rem] items-center gap-3 text-sm">
                    <span className={cn("truncate", k === health.weakest_area ? "font-medium text-foreground" : "text-muted-foreground")}>{FACTOR_LABEL[k] ?? humanize(k)}</span>
                    <ProgressBar value={v} label={FACTOR_LABEL[k] ?? k} />
                    <span className="text-right tabular-nums text-muted-foreground">{Math.round(v)}</span>
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>

          {data.alerts.length > 0 && (
            <Card>
              <CardHeader title="Budget alerts" description="Categories at 75% of their monthly budget or more" icon={<AlertTriangle />} action={<Button asChild variant="ghost" size="sm"><Link to="/app/budgets">Manage budgets</Link></Button>} />
              <CardBody className="grid gap-2 sm:grid-cols-2">
                {data.alerts.map((b) => {
                  const tone = b.percent_used >= 100 ? "danger" : b.percent_used >= 90 ? "warning" : "info";
                  return (
                    <div
                      key={b.id}
                      role="status"
                      className={cn(
                        "flex items-center justify-between gap-3 rounded-xl border px-3 py-2 text-sm",
                        tone === "danger" && "border-danger/30 bg-danger/10 text-danger",
                        tone === "warning" && "border-warning/35 bg-warning/10 text-warning",
                        tone === "info" && "border-info/30 bg-info/10 text-info",
                      )}
                    >
                      <span className="font-medium">{b.category}</span>
                      <span className="tabular-nums">
                        {b.percent_used >= 100 ? `Exceeded (${Math.round(b.percent_used)}%)` : `${Math.round(b.percent_used)}% used`}
                      </span>
                    </div>
                  );
                })}
              </CardBody>
            </Card>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard
              title="Income vs expenses"
              description={`${data.month_name} ${data.year}`}
              icon={<CreditCard />}
              legend={[{ label: "Income", color: "#7C5CFF" }, { label: "Expenses", color: "#F472B6" }]}
              table={{ columns: ["", "Amount"], rows: [["Income", money(m.monthly_income)], ["Expenses", money(m.monthly_expenses)]] }}
            >
              <GroupedBars
                xKey="name"
                data={[{ name: "This month", income: m.monthly_income, expenses: m.monthly_expenses }]}
                series={[{ key: "income", name: "Income", color: "#7C5CFF" }, { key: "expenses", name: "Expenses", color: "#F472B6" }]}
              />
            </ChartCard>

            <ChartCard
              title="Spending by category"
              description="All recorded expenses"
              icon={<PieIcon />}
              empty={charts.category_spend.length ? undefined : "Add expense transactions to see the category breakdown."}
              table={{ columns: ["Category", "Spent"], rows: charts.category_spend.map((c) => [c.category, money(c.amount)]) }}
            >
              <Donut data={charts.category_spend.map((c) => ({ name: c.category, value: c.amount }))} />
            </ChartCard>

            <ChartCard
              title="Monthly trend"
              description="Income and expenses, last six months"
              icon={<TrendingUp />}
              legend={[{ label: "Income", color: "#7C5CFF" }, { label: "Expenses", color: "#22D3EE" }]}
              empty={charts.trend.length > 1 ? undefined : "Add transactions across more than one month to see a trend."}
              table={{ columns: ["Month", "Income", "Expenses"], rows: charts.trend.map((t) => [t.month, money(t.income), money(t.expense)]) }}
            >
              <TrendChart
                data={charts.trend}
                series={[{ key: "income", name: "Income", color: "#7C5CFF", index: 0 }, { key: "expense", name: "Expenses", color: "#22D3EE", index: 1 }]}
              />
            </ChartCard>

            <ChartCard
              title="Investment allocation"
              description="By current value"
              icon={<BarChart3 />}
              empty={
                charts.allocation.length ? undefined : (
                  <span>
                    No investments yet. <Link to="/app/investments" className="font-medium text-violet-ink hover:underline">Add one</Link> to see allocation.
                  </span>
                )
              }
              table={{ columns: ["Asset", "Value"], rows: charts.allocation.map((a) => [a.name, money(a.value)]) }}
            >
              <Donut data={charts.allocation} />
            </ChartCard>

            <ChartCard
              title="Budget vs actual"
              description={`${data.month_name} ${data.year}`}
              icon={<Scale />}
              legend={[{ label: "Budget", color: "#7C5CFF" }, { label: "Actual", color: STATUS.warning }]}
              empty={
                charts.budget_vs_actual.length ? undefined : (
                  <span>
                    No budgets set for this month. <Link to="/app/budgets" className="font-medium text-violet-ink hover:underline">Set one</Link>.
                  </span>
                )
              }
              table={{ columns: ["Category", "Budget", "Actual"], rows: charts.budget_vs_actual.map((b) => [b.category, money(b.budget), money(b.actual)]) }}
            >
              <GroupedBars
                xKey="category"
                data={charts.budget_vs_actual}
                series={[{ key: "budget", name: "Budget", color: "#7C5CFF" }, { key: "actual", name: "Actual", color: STATUS.warning }]}
              />
            </ChartCard>

            <ChartCard
              title="Savings goals progress"
              description="Percent of target saved"
              icon={<Target />}
              empty={
                charts.goals.length ? undefined : (
                  <span>
                    No goals yet. <Link to="/app/goals" className="font-medium text-violet-ink hover:underline">Create a goal</Link> to track progress.
                  </span>
                )
              }
              table={{ columns: ["Goal", "Progress"], rows: charts.goals.map((g) => [g.name, pct(g.percent)]) }}
            >
              <ColorBars data={charts.goals.map((g) => ({ name: g.name, value: g.percent }))} domain={[0, 100]} format={(v) => `${Math.round(v)}%`} name="Progress" />
            </ChartCard>
          </div>
        </div>
      )}
    </>
  );
}

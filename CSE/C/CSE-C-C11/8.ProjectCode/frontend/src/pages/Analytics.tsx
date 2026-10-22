import { Activity, BarChart3, CalendarDays, CheckCircle2, Gauge, PieChart as PieIcon, Receipt, TrendingDown, TrendingUp, Wand2, Wallet, Zap } from "lucide-react";
import { useState } from "react";

import { ChartCard } from "@/components/charts/Chart";
import { ColorBars, Donut, TrendChart } from "@/components/charts/FinanceCharts";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Segmented } from "@/components/ui/Toggles";
import { addDaysISO, pct, todayISO, useMoney } from "@/lib/format";
import { useAnalytics } from "@/lib/queries";
import { cn } from "@/lib/utils";

type TypeFilter = "All" | "income" | "expense";

export default function Analytics() {
  const money = useMoney();
  const [start, setStart] = useState(() => addDaysISO(todayISO(), -90));
  const [end, setEnd] = useState(todayISO);
  const [type, setType] = useState<TypeFilter>("All");
  const rangeInvalid = !!start && !!end && start > end;
  const q = useAnalytics({ start, end, type });
  const incomeView = type === "income";

  return (
    <>
      <PageHeader title="Analytics" description="Dig into a date range, then see what the model expects next month." />

      <Card className="mb-6">
        <CardBody className="flex flex-wrap items-end gap-4">
          <FormField label="From" error={rangeInvalid ? "'From' must be on or before 'To'." : undefined}>
            {(p) => <Input {...p} type="date" icon={<CalendarDays />} value={start} onChange={(e) => setStart(e.target.value)} />}
          </FormField>
          <FormField label="To">{(p) => <Input {...p} type="date" icon={<CalendarDays />} value={end} onChange={(e) => setEnd(e.target.value)} />}</FormField>
          <div className="space-y-1.5">
            <span className="text-sm font-medium text-foreground/90">Category chart shows</span>
            <div>
              <Segmented
                label="Category chart type"
                value={type}
                onChange={setType}
                options={[
                  { value: "All", label: "Spending" },
                  { value: "expense", label: "Expenses" },
                  { value: "income", label: "Income" },
                ]}
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {q.isPending ? (
        <div className="space-y-4" role="status" aria-label="Loading analytics">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-[132px] rounded-2xl" />
            ))}
          </div>
          <Skeleton className="h-72 w-full rounded-2xl" />
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load analytics" onRetry={() => void q.refetch()} hint={rangeInvalid ? "Fix the date range first." : undefined} />
      ) : (
        <div className={cn("space-y-6 transition-opacity", q.isFetching && "opacity-70")}>
          <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StaggerItem>
              <StatCard label="Total income" value={q.data.overview.total_income} format={(n) => money(n)} icon={<Wallet />} accent="cyan" hint="In range" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Total expenses" value={q.data.overview.total_expenses} format={(n) => money(n)} icon={<Receipt />} accent="magenta" hint="In range" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Savings rate" value={q.data.overview.savings_rate} format={(n) => pct(n, 1)} icon={<TrendingUp />} hint="Of income in range" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Avg. daily spending" value={q.data.overview.avg_daily_spending} format={(n) => money(n)} icon={<Gauge />} accent="cyan" hint="Per day in range" />
            </StaggerItem>
            <StaggerItem>
              <StatCard
                label="Largest expense"
                value={q.data.overview.largest_expense?.amount ?? null}
                format={(n) => money(n)}
                display={<span className="text-muted-foreground">None</span>}
                icon={<Zap />}
                accent="magenta"
                hint={q.data.overview.largest_expense ? `${q.data.overview.largest_expense.description}` : "No expenses in range"}
              />
            </StaggerItem>
          </Stagger>
          {q.data.overview.top_category && (
            <p className="text-sm text-muted-foreground">
              Top spending category in this period: <Badge tone="violet">{q.data.overview.top_category}</Badge>
            </p>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard
              title={incomeView ? "Income by category" : "Category distribution"}
              description={`${q.data.range.start} to ${q.data.range.end}`}
              icon={<BarChart3 />}
              empty={q.data.category_distribution.length ? undefined : `No ${incomeView ? "income" : "expense"} data in this range.`}
              table={{ columns: ["Category", "Amount"], rows: q.data.category_distribution.map((c) => [c.category, money(c.amount)]) }}
            >
              <ColorBars data={q.data.category_distribution.map((c) => ({ name: c.category, value: c.amount }))} format={(v) => money.compact(v)} name="Amount" />
            </ChartCard>

            <ChartCard
              title="Income vs expenses"
              description="Share of money moved in this range"
              icon={<PieIcon />}
              empty={q.data.income_expense_split.length ? undefined : "No transactions in this range."}
              table={{ columns: ["Type", "Amount"], rows: q.data.income_expense_split.map((s) => [s.transaction_type, money(s.amount)]) }}
            >
              <Donut data={q.data.income_expense_split.map((s) => ({ name: s.transaction_type === "income" ? "Income" : "Expenses", value: s.amount }))} />
            </ChartCard>
          </div>

          <ChartCard
            title="Spending trend"
            description="Expenses by month (last six months with data)"
            icon={<Activity />}
            empty={q.data.trend.length > 1 ? undefined : "Add transactions across more than one month to see a trend."}
            table={{ columns: ["Month", "Expenses"], rows: q.data.trend.map((t) => [t.month, money(t.expense)]) }}
          >
            <TrendChart data={q.data.trend} series={[{ key: "expense", name: "Expenses", color: "#7C5CFF", index: 0 }]} />
          </ChartCard>

          <Card>
            <CardHeader title="Spending prediction (ML)" description="A linear trend over your monthly totals. It declines to guess without enough history." icon={<Wand2 />} />
            <CardBody className="space-y-4">
              {!q.data.prediction.available ? (
                <p role="status" className="rounded-xl border border-info/30 bg-info/10 px-4 py-3 text-sm text-info">
                  {q.data.prediction.message}
                </p>
              ) : (
                <>
                  <div className="grid gap-4 sm:grid-cols-3">
                    <StatCard label="Predicted next-month expense" value={q.data.prediction.predicted_next_month_expense} format={(n) => money(n)} icon={<Wand2 />} hint={`From ${q.data.prediction.months_used} months`} />
                    <StatCard label="Recent 3-month average" value={q.data.prediction.recent_average} format={(n) => money(n)} icon={<Activity />} accent="cyan" />
                    <StatCard
                      label="Trend"
                      display={<span className="capitalize">{q.data.prediction.trend}</span>}
                      icon={q.data.prediction.trend === "decreasing" ? <TrendingDown /> : <TrendingUp />}
                      accent="magenta"
                      hint={q.data.prediction.trend === "increasing" ? "Spending is creeping up" : q.data.prediction.trend === "decreasing" ? "Spending is easing" : "Spending is steady"}
                    />
                  </div>
                  {q.data.category_prediction.available ? (
                    q.data.overrun_risks.length ? (
                      <div className="space-y-2" role="status">
                        <p className="text-sm font-medium text-warning">Predicted potential budget overruns next month</p>
                        <ul className="grid gap-2 sm:grid-cols-2">
                          {q.data.overrun_risks.map((r) => (
                            <li key={r.category} className="rounded-xl border border-warning/35 bg-warning/10 px-3 py-2 text-sm">
                              <span className="font-medium">{r.category}</span>: predicted {money(r.predicted_spend)} vs budget {money(r.budget)}
                              <span className="text-warning"> (over by {money(r.overrun_amount)})</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <p role="status" className="flex items-center gap-2 rounded-xl border border-success/30 bg-success/10 px-4 py-3 text-sm text-success">
                        <CheckCircle2 className="size-4" /> No predicted budget overruns based on current trends.
                      </p>
                    )
                  ) : (
                    <p className="text-xs text-muted-foreground">{q.data.category_prediction.message}</p>
                  )}
                </>
              )}
            </CardBody>
          </Card>
        </div>
      )}
    </>
  );
}

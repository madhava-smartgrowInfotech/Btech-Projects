import {
  ArrowRight,
  BadgeCheck,
  ClipboardCheck,
  FileText,
  Gauge,
  MessageSquareText,
  ShieldAlert,
  Timer,
  Upload,
} from "lucide-react";
import { motion } from "motion/react";
import { Link } from "react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { axisProps, ChartCard, ChartTooltip } from "@/components/charts/ChartCard";
import { verdictMeta } from "@/components/common/Badges";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/States";
import { StatTile } from "@/components/common/StatTile";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import { useDashboard } from "@/lib/queries";
import type { Verdict } from "@/lib/types";
import { formatMs, timeAgo } from "@/lib/utils";

const verdictColor: Record<Verdict, string> = {
  covered: "var(--status-good)",
  partly_covered: "var(--status-warning)",
  not_covered: "var(--status-critical)",
  needs_info: "var(--status-neutral)",
};

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

function shortDate(iso: string) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useDashboard();

  return (
    <div>
      <PageHeader
        title={`${greeting()}, ${user?.full_name.split(" ")[0] ?? ""}`}
        description="Your policies at a glance: what you asked, how well answers were supported, and what to watch out for."
        actions={
          <>
            <Button asChild variant="outline">
              <Link to="/app/policies">
                <Upload /> Upload policy
              </Link>
            </Button>
            <Button asChild>
              <Link to="/app/chat">
                <MessageSquareText /> Ask a question
              </Link>
            </Button>
          </>
        }
      />

      {error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : isLoading || !data ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-72 rounded-xl" />
            <Skeleton className="h-72 rounded-xl" />
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
            <StatTile label="Policies" value={data.kpis.policies} icon={<FileText />} hint={`${data.kpis.ready_policies} ready`} />
            <StatTile label="Questions" value={data.kpis.questions} icon={<MessageSquareText />} hint="answered with citations" />
            <StatTile
              label="Faithfulness"
              value={data.kpis.avg_faithfulness}
              suffix="/100"
              decimals={0}
              icon={<BadgeCheck />}
              hint="average support score"
            />
            <StatTile
              label="Response"
              value={data.kpis.median_response_ms ? data.kpis.median_response_ms / 1000 : null}
              suffix="s"
              decimals={1}
              icon={<Timer />}
              hint="median answer time"
            />
            <StatTile label="Claim checks" value={data.kpis.claim_checks} icon={<ClipboardCheck />} hint={`${data.kpis.comparisons} comparisons`} />
            <StatTile label="High risks" value={data.kpis.high_risks} icon={<ShieldAlert />} hint="across your policies" />
          </div>

          {data.kpis.policies === 0 && <GetStarted />}

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard
              title="Activity"
              description="Questions and claim checks, last 14 days"
              legend={[
                { label: "Questions", color: "var(--series-1)" },
                { label: "Claim checks", color: "var(--series-2)" },
              ]}
              table={{
                columns: ["Date", "Questions", "Claim checks"],
                rows: data.activity_by_day.map((d) => [shortDate(d.date), d.questions, d.claim_checks]),
              }}
              empty={
                data.activity_by_day.every((d) => d.questions + d.claim_checks === 0)
                  ? "No activity yet - ask a question or run a claim check to see it here."
                  : undefined
              }
            >
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.activity_by_day} barGap={2} margin={{ left: -20, right: 4, top: 4 }}>
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="date" tickFormatter={shortDate} {...axisProps} minTickGap={16} />
                  <YAxis allowDecimals={false} {...axisProps} />
                  <Tooltip
                    cursor={{ fill: "var(--muted)", opacity: 0.5 }}
                    content={<ChartTooltip labelFormatter={(l) => shortDate(String(l))} />}
                  />
                  <Bar dataKey="questions" name="Questions" fill="var(--series-1)" radius={[4, 4, 0, 0]} maxBarSize={14} />
                  <Bar dataKey="claim_checks" name="Claim checks" fill="var(--series-2)" radius={[4, 4, 0, 0]} maxBarSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Answer faithfulness"
              description="How well each answer is supported by the clauses it cites"
              table={{ columns: ["Score band", "Answers"], rows: data.faithfulness_bins.map((b) => [b.bin, b.count]) }}
              empty={data.kpis.questions === 0 ? "Ask your first question to see how well answers are supported." : undefined}
            >
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data.faithfulness_bins} margin={{ left: -20, right: 4, top: 16 }}>
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="bin" {...axisProps} />
                  <YAxis allowDecimals={false} {...axisProps} />
                  <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip labelFormatter={(l) => `Score ${l}`} />} />
                  <Bar
                    dataKey="count"
                    name="Answers"
                    fill="var(--series-1)"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={48}
                    label={{ position: "top", fontSize: 11, fill: "var(--muted-foreground)" }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Risks by policy"
              description="Flagged gotchas by severity"
              legend={[
                { label: "High", color: "var(--status-critical)" },
                { label: "Medium", color: "var(--status-warning)" },
                { label: "Low", color: "var(--status-neutral)" },
              ]}
              table={{
                columns: ["Policy", "High", "Medium", "Low"],
                rows: data.risks_by_policy.map((r) => [r.policy, r.high, r.medium, r.low]),
              }}
              empty={data.risks_by_policy.length === 0 ? "Risk highlights appear once a policy has been processed." : undefined}
            >
              <ResponsiveContainer width="100%" height={Math.max(160, data.risks_by_policy.length * 44 + 30)}>
                <BarChart data={data.risks_by_policy} layout="vertical" margin={{ left: 8, right: 12 }}>
                  <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
                  <XAxis type="number" allowDecimals={false} {...axisProps} />
                  <YAxis
                    type="category"
                    dataKey="policy"
                    width={120}
                    {...axisProps}
                    tickFormatter={(v: string) => (v.length > 18 ? `${v.slice(0, 17)}…` : v)}
                  />
                  <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip />} />
                  <Bar dataKey="high" name="High" stackId="s" fill="var(--status-critical)" stroke="var(--card)" strokeWidth={2} maxBarSize={20} />
                  <Bar dataKey="medium" name="Medium" stackId="s" fill="var(--status-warning)" stroke="var(--card)" strokeWidth={2} maxBarSize={20} />
                  <Bar dataKey="low" name="Low" stackId="s" fill="var(--status-neutral)" stroke="var(--card)" strokeWidth={2} radius={[0, 4, 4, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard
              title="Response time"
              description="Seconds per answer, most recent 20"
              table={{
                columns: ["Answer", "Seconds", "Faithfulness"],
                rows: data.response_times.map((r) => [r.n, (r.ms / 1000).toFixed(1), r.faithfulness ?? "-"]),
              }}
              empty={data.response_times.length < 2 ? "Response times appear after a couple of answers." : undefined}
            >
              <ResponsiveContainer width="100%" height={220}>
                <LineChart
                  data={data.response_times.map((r) => ({ ...r, s: +(r.ms / 1000).toFixed(2) }))}
                  margin={{ left: -20, right: 8, top: 8 }}
                >
                  <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
                  <XAxis dataKey="n" {...axisProps} />
                  <YAxis {...axisProps} unit="s" />
                  <Tooltip
                    cursor={{ stroke: "var(--muted-foreground)", strokeDasharray: "3 3" }}
                    content={<ChartTooltip labelFormatter={(l) => `Answer ${l}`} formatter={(v) => `${v} s`} />}
                  />
                  <Line
                    type="monotone"
                    dataKey="s"
                    name="Response time"
                    stroke="var(--series-1)"
                    strokeWidth={2}
                    dot={{ r: 4, strokeWidth: 2, stroke: "var(--card)", fill: "var(--series-1)" }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <ChartCard
              title="Claim Copilot verdicts"
              description="Outcome of your claim checks"
              className="lg:col-span-1"
              table={{ columns: ["Verdict", "Checks"], rows: data.verdicts.map((v) => [verdictMeta[v.verdict].label, v.count]) }}
              empty={data.verdicts.length === 0 ? "Run a claim check to see verdicts here." : undefined}
            >
              <ResponsiveContainer width="100%" height={Math.max(140, data.verdicts.length * 40 + 20)}>
                <BarChart
                  data={data.verdicts.map((v) => ({ ...v, label: verdictMeta[v.verdict].label }))}
                  layout="vertical"
                  margin={{ left: 8, right: 28 }}
                >
                  <XAxis type="number" hide allowDecimals={false} />
                  <YAxis type="category" dataKey="label" width={112} {...axisProps} />
                  <Tooltip cursor={{ fill: "var(--muted)", opacity: 0.5 }} content={<ChartTooltip />} />
                  <Bar
                    dataKey="count"
                    name="Checks"
                    radius={[0, 4, 4, 0]}
                    maxBarSize={18}
                    label={{ position: "right", fontSize: 11, fill: "var(--muted-foreground)" }}
                  >
                    {data.verdicts.map((v) => (
                      <Cell key={v.verdict} fill={verdictColor[v.verdict]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">Recent activity</CardTitle>
              </CardHeader>
              <CardContent>
                {data.recent.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nothing yet. Your uploads, questions and claim checks will appear here.</p>
                ) : (
                  <ul className="divide-y">
                    {data.recent.map((r, i) => (
                      <motion.li
                        key={`${r.link}-${i}`}
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.03 }}
                      >
                        <Link to={r.link} className="flex items-center gap-3 py-2.5 text-sm hover:text-primary">
                          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground [&_svg]:size-4">
                            {r.type === "policy" ? <FileText /> : r.type === "claim" ? <ClipboardCheck /> : <MessageSquareText />}
                          </span>
                          <span className="min-w-0 flex-1 truncate">{r.title}</span>
                          <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(r.at)}</span>
                        </Link>
                      </motion.li>
                    ))}
                  </ul>
                )}
                <div className="mt-4 flex items-center gap-2 rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground">
                  <Gauge className="size-4 shrink-0" />
                  {data.kpis.ai_calls} AI requests so far ({data.kpis.ai_tokens.toLocaleString("en-IN")} tokens). Median answer time{" "}
                  {formatMs(data.kpis.median_response_ms)}.
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function GetStarted() {
  const steps = [
    { title: "Add a policy", text: "Upload your policy wording PDF, or add the sample policies.", to: "/app/policies", icon: Upload },
    { title: "Ask anything", text: "“Is cataract surgery covered and after how long?”", to: "/app/chat", icon: MessageSquareText },
    { title: "Check a claim", text: "Get a verdict, document checklist and claim steps.", to: "/app/claims", icon: ClipboardCheck },
  ];
  return (
    <Card className="border-primary/30 bg-gradient-to-br from-accent/60 to-transparent">
      <CardHeader>
        <CardTitle>Get started in three steps</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-3">
        {steps.map((s, i) => (
          <Link key={s.title} to={s.to} className="group rounded-xl border bg-card p-4 transition-colors hover:border-primary/50">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <span className="grid size-6 place-items-center rounded-full bg-primary text-xs text-primary-foreground">{i + 1}</span>
              {s.title}
            </div>
            <p className="text-sm text-muted-foreground">{s.text}</p>
            <span className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary">
              Go <ArrowRight className="size-3 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}

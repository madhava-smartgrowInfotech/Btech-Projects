import { useQuery } from "@tanstack/react-query";
import { BarChart3, ClipboardCheck, FileText, MessageSquareText, Route, UploadCloud } from "lucide-react";
import { Link } from "react-router";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps, STATUS } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { CardsSkeleton, EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { api, type Dashboard as DashboardData } from "@/lib/api";
import { keys } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

const barColor = (accuracy: number) => (accuracy < 50 ? STATUS.critical : accuracy < 80 ? STATUS.warning : STATUS.good);

export default function Dashboard() {
  const query = useQuery({ queryKey: keys.dashboard, queryFn: async () => (await api.get<DashboardData>("/dashboard")).data });

  if (query.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading dashboard">
        <Skeleton className="h-10 w-72" />
        <CardsSkeleton count={3} />
        <div className="grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-72 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl" />
        </div>
      </div>
    );
  }
  if (query.isError) return <ErrorState error={query.error} title="Couldn't load your dashboard" onRetry={() => query.refetch()} />;

  const d = query.data;
  const chartData = d.performance.map((p) => ({ subject: p.subject, accuracy: p.accuracy, attempts: p.attempts }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome back, ${d.username}`}
        description="Your uploads, questions and quiz results at a glance."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link to="/app/ask">
                <MessageSquareText /> Ask a question
              </Link>
            </Button>
            <Button asChild>
              <Link to="/app/upload">
                <UploadCloud /> Upload material
              </Link>
            </Button>
          </>
        }
      />

      <Stagger className="grid gap-4 sm:grid-cols-3">
        <StaggerItem>
          <StatCard label="Documents uploaded" value={d.doc_count} icon={<FileText />} accent="violet" />
        </StaggerItem>
        <StaggerItem>
          <StatCard label="Questions asked" value={d.query_count} icon={<MessageSquareText />} accent="cyan" />
        </StaggerItem>
        <StaggerItem>
          <StatCard label="Quiz questions attempted" value={d.quiz_attempts} icon={<ClipboardCheck />} accent="magenta" />
        </StaggerItem>
      </Stagger>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard
          title="Subject-wise performance"
          description="Quiz accuracy per subject"
          icon={<BarChart3 />}
          legend={[
            { label: "Below 50%", color: STATUS.critical },
            { label: "50-79%", color: STATUS.warning },
            { label: "80% and above", color: STATUS.good },
          ]}
          table={{ columns: ["Subject", "Accuracy %", "Questions"], rows: chartData.map((r) => [r.subject, r.accuracy, r.attempts]) }}
          empty={
            chartData.length === 0 ? (
              <div className="space-y-3">
                <p>Take a quiz to see your performance analytics here.</p>
                <Button asChild size="sm">
                  <Link to="/app/quiz">Take a quiz</Link>
                </Button>
              </div>
            ) : undefined
          }
        >
          <div className="h-60 w-full" role="img" aria-label={`Bar chart of quiz accuracy for ${chartData.length} subjects`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                <ChartGradients />
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="subject" {...axisProps} interval={0} tickFormatter={(v: string) => (v.length > 18 ? `${v.slice(0, 17)}…` : v)} />
                <YAxis {...axisProps} domain={[0, 100]} unit="%" />
                <Tooltip
                  cursor={{ fill: "var(--muted)" }}
                  content={<ChartTooltip formatter={(v) => `${v}%`} />}
                />
                <Bar dataKey="accuracy" name="Accuracy" radius={[8, 8, 0, 0]} maxBarSize={56}>
                  {chartData.map((r) => (
                    <Cell key={r.subject} fill={barColor(r.accuracy)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <Card className="flex flex-col">
          <CardHeader
            title="Recent documents"
            description="Your five latest uploads"
            icon={<FileText />}
            action={
              d.documents.length > 0 ? (
                <Button asChild variant="ghost" size="sm">
                  <Link to="/app/documents">View all</Link>
                </Button>
              ) : undefined
            }
          />
          <CardBody className="flex-1 pt-3">
            {d.documents.length === 0 ? (
              <EmptyState
                className="py-8"
                icon={<UploadCloud />}
                title="No documents yet"
                description="Upload a PDF, DOCX or TXT and it appears here with its detected topics."
                action={
                  <Button asChild size="sm">
                    <Link to="/app/upload">Upload one now</Link>
                  </Button>
                }
              />
            ) : (
              <ul className="divide-y divide-[var(--glass-border)]">
                {d.documents.map((doc) => (
                  <li key={doc.id} className="flex items-center justify-between gap-3 py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink">
                        <FileText className="size-4" />
                      </span>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium">{doc.filename}</div>
                        <div className="text-xs text-muted-foreground">{formatDate(doc.uploaded_at)}</div>
                      </div>
                    </div>
                    <Badge tone="violet">{doc.subject}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardBody className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h3 className="font-display font-semibold">See where to focus next</h3>
            <p className="text-sm text-muted-foreground">Your roadmap ranks topics by how often you get them wrong.</p>
          </div>
          <Button asChild variant="secondary">
            <Link to="/app/roadmap">
              <Route /> View roadmap
            </Link>
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}


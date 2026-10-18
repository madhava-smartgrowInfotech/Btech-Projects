import { useQueryClient } from "@tanstack/react-query";
import { Activity, FlaskConical, GitPullRequest, History, MessagesSquare, OctagonAlert, Play, ShieldAlert, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router";

import { AgentProgress } from "@/components/app/Bits";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard, Timeline } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { verdictLabel } from "@/lib/domain";
import { useMeta, useReviews, startReview } from "@/lib/hooks";
import { useJob } from "@/lib/jobs";
import { keys } from "@/lib/queries";
import { useSettings } from "@/lib/settings";
import { cn, timeAgo } from "@/lib/utils";

const CARDS = [
  { icon: GitPullRequest, title: "PR review", text: "Paste a diff, compare two versions, drop a GitHub PR link or upload a repo. Get a verdict, risk score, explanations and patches in seconds.", to: "/app/review", cta: "Review a pull request" },
  { icon: MessagesSquare, title: "Codebase assistant", text: "Ask “where is authentication handled?” or “which files define the routes?”. Graph-based retrieval answers with files, functions and call flow.", to: "/app/codebase", cta: "Ask your codebase" },
  { icon: FlaskConical, title: "Model lab", text: "Reproduces the base paper: 14 metrics, 7 feature-selection methods, SmoteTomek, 9 models and vulnerability-type classification.", to: "/app/lab", cta: "Explore the model" },
];

const verdictTone = { BLOCK: "danger", REQUEST_CHANGES: "warning", APPROVE: "success" } as const;

export default function Overview() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const meta = useMeta();
  const reviews = useReviews();
  const { options } = useSettings();
  const job = useJob<{ review_id: string }>();

  async function runDemo() {
    const done = await job.run(() => startReview({ kind: "demo-diff", options: options(meta.data?.llm_env ?? false) }));
    if (!done?.result) return;
    await qc.invalidateQueries({ queryKey: keys.reviews });
    toast.success(`Demo review finished in ${done.seconds?.toFixed(1)} s`);
    navigate(`/app/review/${done.result.review_id}`);
  }

  const rows = reviews.data ?? [];
  const chronological = [...rows].reverse().map((r) => r.score);
  const avg = rows.length ? Math.round(rows.reduce((s, r) => s + r.score, 0) / rows.length) : null;
  const blocked = rows.filter((r) => r.verdict === "BLOCK").length;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Overview"
        title="Autonomous pull-request security review"
        description="AutoSecAI reads every pull request like a security engineer: static analysis finds the flaws, the base-paper metric model flags risky functions, each issue is explained in plain language, and patches are verified before they are offered."
      />

      <Stagger className="grid gap-4 md:grid-cols-3">
        {CARDS.map(({ icon: Icon, title, text, to, cta }) => (
          <StaggerItem key={title}>
            <Card interactive className="flex h-full flex-col gap-3 p-5">
              <span className="grid size-10 place-items-center rounded-xl bg-grad-primary text-white">
                <Icon className="size-5" />
              </span>
              <h2 className="font-display text-lg font-semibold">{title}</h2>
              <p className="flex-1 text-sm text-muted-foreground">{text}</p>
              <Button variant="secondary" onClick={() => navigate(to)}>{cta}</Button>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>

      <section aria-labelledby="pipe-title" className="space-y-4">
        <h2 id="pipe-title" className="font-display text-xl font-semibold">How the agents work together</h2>
        {meta.isPending ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" role="status" aria-label="Loading pipeline">
            {Array.from({ length: 7 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
          </div>
        ) : meta.isError ? (
          <ErrorState error={meta.error} title="Couldn't load the agent pipeline" onRetry={() => meta.refetch()} />
        ) : (
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {meta.data.pipeline.map((s, i) => (
              <li key={s.name} className="glass flex gap-3 rounded-2xl p-4">
                <span className="grid size-8 shrink-0 place-items-center rounded-full bg-grad-primary text-sm font-semibold text-white">{i + 1}</span>
                <span className="min-w-0">
                  <span className="block font-medium">{s.name}</span>
                  <span className="block text-xs text-muted-foreground">{s.text}</span>
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>

      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-5">
          <Card className="space-y-4 p-5">
            <div className="space-y-1">
              <h2 className="font-display text-lg font-semibold">Try it in one click</h2>
              <p className="text-sm text-muted-foreground">Load a deliberately vulnerable Flask pull request and watch the agents work.</p>
            </div>
            {job.running ? (
              <AgentProgress messages={job.messages} />
            ) : (
              <Button onClick={runDemo} disabled={!meta.data}>
                <Play /> Run demo pull request review
              </Button>
            )}
            {job.error && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                The demo review failed: {job.error}
              </p>
            )}
          </Card>

          <Card>
            <CardHeader title="Recent reviews" icon={<History />} action={<Button variant="ghost" size="sm" onClick={() => navigate("/app/history")}>All history</Button>} />
            <CardBody>
              {reviews.isPending ? (
                <div className="space-y-3" role="status" aria-label="Loading reviews">
                  {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12" />)}
                </div>
              ) : reviews.isError ? (
                <ErrorState error={reviews.error} title="Couldn't load your reviews" onRetry={() => reviews.refetch()} />
              ) : rows.length === 0 ? (
                <EmptyState
                  icon={<ShieldCheck />}
                  title="No reviews yet"
                  description="Run the demo above or review your own pull request. Each review is saved here."
                  action={<Button onClick={() => navigate("/app/review")}>Review a pull request</Button>}
                />
              ) : (
                <Timeline
                  items={rows.slice(0, 5).map((r) => ({
                    icon: r.verdict === "BLOCK" ? <OctagonAlert /> : r.verdict === "APPROVE" ? <ShieldCheck /> : <ShieldAlert />,
                    title: r.title,
                    meta: `${timeAgo(r.created)} · ${r.findings} findings · ${r.source}`,
                    trailing: <Badge tone={verdictTone[r.verdict]}>{verdictLabel(r.verdict)} · {r.score}</Badge>,
                    onClick: () => navigate(`/app/review/${r.id}`),
                  }))}
                />
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-4">
          <h2 className="font-display text-lg font-semibold">Your activity</h2>
          {reviews.isPending ? (
            <div className="grid gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
          ) : (
            <div className={cn("grid gap-4", rows.length === 0 && "opacity-70")}>
              <StatCard label="Reviews" value={rows.length} icon={<Activity />} spark={chronological} hint={rows.length ? "saved in your history" : "run the demo to get started"} />
              <StatCard label="Average risk" value={avg} display={avg === null ? "-" : undefined} icon={<ShieldAlert />} accent="cyan" hint="0 safe · 100 critical" />
              <StatCard label="Blocked" value={blocked} icon={<OctagonAlert />} accent="magenta" hint={rows.length ? `of ${rows.length} reviews` : undefined} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

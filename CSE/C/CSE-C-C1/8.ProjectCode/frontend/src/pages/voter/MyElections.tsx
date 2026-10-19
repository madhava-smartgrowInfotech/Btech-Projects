import { BadgeCheck, BarChart3, CalendarClock, Lock, ShieldCheck, Vote } from "lucide-react";
import { Link } from "react-router";

import { Hash, StatusBadge } from "@/components/domain/common";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useAuth } from "@/lib/auth";
import { useVoterElections } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export default function MyElections() {
  const { user } = useAuth();
  const q = useVoterElections();

  const header = (
    <PageHeader
      eyebrow="Voter"
      title={`Welcome, ${user?.display_name ?? "voter"}`}
      description="Pick an open election, verify your identity and cast one encrypted ballot."
      actions={<Badge tone="warning">Demo verification environment</Badge>}
    />
  );

  if (q.isPending) {
    return <>{header}<div className="grid gap-4 md:grid-cols-2" role="status" aria-label="Loading elections">{[0, 1].map((i) => <Skeleton key={i} className="h-52 rounded-2xl" />)}</div></>;
  }
  if (q.isError) return <>{header}<ErrorState error={q.error} title="Could not load your elections" onRetry={() => q.refetch()} /></>;
  if (q.data.length === 0) {
    return (
      <>
        {header}
        <EmptyState
          icon={<Vote />}
          title="No elections to vote in yet"
          description="Elections show up here once an administrator opens them. Check back soon."
          action={<Button variant="secondary" onClick={() => q.refetch()}>Refresh</Button>}
        />
      </>
    );
  }

  return (
    <>
      {header}
      <Stagger className="grid gap-4 md:grid-cols-2">
        {q.data.map((e) => (
          <StaggerItem key={e.id}>
            <Card className="flex h-full flex-col gap-4 p-5">
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-display text-lg font-semibold leading-tight">{e.title}</h2>
                <StatusBadge status={e.status} />
              </div>
              {e.description && <p className="text-sm text-muted-foreground">{e.description}</p>}
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <CalendarClock className="size-3.5 shrink-0" /> {formatDate(e.start_time, true)} to {formatDate(e.end_time, true)}
              </p>

              {e.voted && e.ballot_id && (
                <div className="flex items-start gap-2 rounded-xl border border-success/30 bg-success/10 p-3 text-sm">
                  <BadgeCheck className="mt-0.5 size-4 shrink-0 text-success" />
                  <div className="min-w-0">
                    <div className="font-medium text-success">Vote confirmed</div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">Receipt <Hash value={e.ballot_id} head={12} tail={4} /></div>
                  </div>
                </div>
              )}

              <div className="mt-auto flex flex-wrap items-center gap-2 border-t border-[var(--glass-border)] pt-4">
                {!e.voted && e.status === "OPEN" && (
                  <Button asChild><Link to={`/app/voter/${e.id}/verify`}><ShieldCheck /> Verify and vote</Link></Button>
                )}
                {e.voted && e.status !== "CLOSED" && <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground"><Lock className="size-4" /> Your ballot is sealed. Results appear when the election closes.</span>}
                {!e.voted && e.status === "PAUSED" && <Badge tone="warning">Voting is paused</Badge>}
                {!e.voted && e.status === "DRAFT" && <Badge tone="info">Not open yet</Badge>}
                {e.status === "CLOSED" && (
                  <Button asChild variant="secondary" magnetic={false}><Link to={`/app/results/${e.id}`}><BarChart3 /> View results</Link></Button>
                )}
                {!e.voted && e.status === "CLOSED" && <span className="text-xs text-muted-foreground">You did not vote in this election.</span>}
              </div>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>
    </>
  );
}

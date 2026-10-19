import { ArrowLeft, Hourglass } from "lucide-react";
import { Link, useParams } from "react-router";

import { ResultsView } from "@/components/domain/ResultsView";
import { StatusBadge } from "@/components/domain/common";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { useAuth } from "@/lib/auth";
import { useResults } from "@/lib/queries";
import axios from "axios";

export default function Results() {
  const id = Number(useParams().id);
  const { user } = useAuth();
  const q = useResults(id);
  useBreadcrumb(q.data?.election.title);
  const back = user?.role === "ADMIN" ? `/app/admin/elections/${id}` : "/app/voter";

  const backButton = (
    <Button asChild variant="secondary" magnetic={false}>
      <Link to={back}><ArrowLeft /> {user?.role === "ADMIN" ? "Back to election" : "Back to my elections"}</Link>
    </Button>
  );

  if (q.isPending) {
    return (
      <>
        <PageHeader title="Results" />
        <div className="space-y-4" role="status" aria-label="Loading results">
          <Skeleton className="h-72 rounded-2xl" />
          <Skeleton className="h-40 rounded-2xl" />
        </div>
      </>
    );
  }
  if (q.isError) {
    const notPublished = axios.isAxiosError(q.error) && q.error.response?.status === 404;
    return (
      <>
        <PageHeader title="Results" actions={backButton} />
        {notPublished ? (
          <EmptyState
            icon={<Hourglass />}
            title="Results are not published yet"
            description="Results appear once the administrator closes the election."
            action={backButton}
          />
        ) : (
          <ErrorState error={q.error} title="Could not load the results" onRetry={() => q.refetch()} />
        )}
      </>
    );
  }
  const { election } = q.data;
  return (
    <>
      <PageHeader
        eyebrow="Results"
        title={election.title}
        description={
          <span className="inline-flex flex-wrap items-center gap-2">
            <StatusBadge status={election.status} />
            {election.status !== "CLOSED" && <span>Provisional tally. Final results are published when the election closes.</span>}
          </span>
        }
        actions={backButton}
      />
      <ResultsView tally={q.data} />
    </>
  );
}

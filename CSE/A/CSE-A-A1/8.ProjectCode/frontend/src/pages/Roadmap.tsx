import { useQuery } from "@tanstack/react-query";
import { ClipboardCheck, Route as RouteIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";

import { Stagger, StaggerItem } from "@/components/motion";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Display";
import { CardsSkeleton, EmptyState, ErrorState, ProgressBar } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";
import { Segmented } from "@/components/ui/Toggles";
import { api, type RoadmapItem } from "@/lib/api";
import { keys } from "@/lib/queries";

const TONE: Record<RoadmapItem["priority"], BadgeTone> = { High: "danger", Medium: "warning", Low: "success" };
const RANK: Record<RoadmapItem["priority"], number> = { High: 0, Medium: 1, Low: 2 };
type Filter = "All" | RoadmapItem["priority"];

export default function Roadmap() {
  const [filter, setFilter] = useState<Filter>("All");
  const query = useQuery({ queryKey: keys.roadmap, queryFn: async () => (await api.get<RoadmapItem[]>("/roadmap")).data });

  const counts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 };
    for (const i of query.data ?? []) c[i.priority] += 1;
    return c;
  }, [query.data]);
  const rows = useMemo(() => (query.data ?? []).filter((i) => filter === "All" || i.priority === filter), [query.data, filter]);

  const columns: Column<RoadmapItem>[] = [
    {
      key: "priority",
      header: "Priority",
      sortValue: (i) => RANK[i.priority],
      cell: (i) => <Badge tone={TONE[i.priority]}>{i.priority}</Badge>,
    },
    { key: "topic", header: "Topic", sortValue: (i) => i.topic, cell: (i) => <span className="font-medium">{i.topic}</span> },
    { key: "subject", header: "Subject", sortValue: (i) => i.subject, cell: (i) => <Badge tone="violet">{i.subject}</Badge> },
    {
      key: "accuracy",
      header: "Accuracy",
      sortValue: (i) => i.accuracy,
      cell: (i) => (
        <span className="flex items-center gap-3 sm:min-w-44">
          <ProgressBar value={i.accuracy} label={`${i.topic} accuracy`} className="w-24 flex-none sm:w-28" />
          <span className="tabular-nums">{i.accuracy}%</span>
        </span>
      ),
    },
    { key: "attempts", header: "Attempts", align: "right", sortValue: (i) => i.attempts, cell: (i) => <span className="tabular-nums">{i.attempts}</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Roadmap"
        title="Your personalized learning roadmap"
        description="Ranked by priority: the weakest topics, based on your quiz accuracy, come first."
        actions={
          <Button asChild variant="secondary">
            <Link to="/app/quiz">
              <ClipboardCheck /> Take a quiz
            </Link>
          </Button>
        }
      />

      {query.isPending ? (
        <CardsSkeleton count={3} />
      ) : query.isError ? (
        <ErrorState error={query.error} title="Couldn't load your roadmap" onRetry={() => query.refetch()} />
      ) : query.data.length === 0 ? (
        <EmptyState
          icon={<RouteIcon />}
          title="No roadmap yet"
          description="Take a quiz so we can see which topics you find hard. Your weakest ones will be listed here."
          action={
            <Button asChild>
              <Link to="/app/quiz">Take a quiz</Link>
            </Button>
          }
        />
      ) : (
        <>
          <Stagger className="grid gap-4 sm:grid-cols-3">
            <StaggerItem>
              <StatCard label="High priority" value={counts.High} hint="Under 50% accuracy" accent="magenta" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Medium priority" value={counts.Medium} hint="50-79% accuracy" accent="violet" />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Low priority" value={counts.Low} hint="80% and above" accent="cyan" />
            </StaggerItem>
          </Stagger>

          <Segmented<Filter>
            label="Filter by priority"
            value={filter}
            onChange={setFilter}
            options={[
              { value: "All", label: `All (${query.data.length})` },
              { value: "High", label: `High (${counts.High})` },
              { value: "Medium", label: `Medium (${counts.Medium})` },
              { value: "Low", label: `Low (${counts.Low})` },
            ]}
          />

          <Table
            caption="Topics ranked by priority"
            columns={columns}
            rows={rows}
            rowKey={(i) => `${i.subject}:${i.topic}`}
            pageSize={12}
            initialSort={{ key: "priority", dir: "asc" }}
            empty={
              <EmptyState
                icon={<RouteIcon />}
                title={`No ${filter.toLowerCase()} priority topics`}
                description="Nothing falls in this group right now."
                action={
                  <Button variant="secondary" onClick={() => setFilter("All")}>
                    Show all topics
                  </Button>
                }
              />
            }
          />
        </>
      )}
    </div>
  );
}

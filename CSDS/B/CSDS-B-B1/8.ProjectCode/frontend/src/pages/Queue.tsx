import { Camera, ChevronRight, Inbox, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { PriorityBadge, SampleBadge, SlaFlag, StatusBadge } from "@/components/domain/Badges";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { Select } from "@/components/ui/Select";
import { days, pct, timeAgo } from "@/lib/format";
import { useMeta, useQueue } from "@/lib/queries";
import type { QueueItem, Status } from "@/lib/types";
import { cn } from "@/lib/utils";

const TABS: { value: Status; label: string }[] = [
  { value: "Submitted", label: "Awaiting review" },
  { value: "Assigned", label: "Assigned" },
  { value: "In Progress", label: "In progress" },
  { value: "Resolved", label: "Resolved" },
  { value: "Rejected", label: "Rejected" },
];
const ALL = "__all__";
const PRIORITIES = ["Critical", "High", "Medium", "Low"];

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

function Row({ c, status }: { c: QueueItem; status: Status }) {
  const cur = c.current;
  const closed = c.status === "Resolved" || c.status === "Rejected";
  return (
    <Link
      to={`/app/complaints/${c.id}`}
      className="glass sweep flex items-center gap-4 rounded-2xl p-4 transition-[transform,border-color] hover:-translate-y-0.5 hover:border-[color-mix(in_srgb,var(--violet)_40%,var(--glass-border))]"
    >
      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
          <PriorityBadge priority={cur.priority} />
          <span className="font-mono text-xs font-semibold">{c.tracking_id}</span>
          {status !== "Submitted" && <StatusBadge status={c.status} />}
          <span className="text-xs text-muted-foreground">
            {c.ward || "No location"} · {c.language} · {timeAgo(c.created_at)}
          </span>
          {c.has_photo && <Camera className="size-3.5 text-muted-foreground" aria-label="Has photo" />}
          <SampleBadge show={c.is_sample} />
        </div>
        <p className="line-clamp-2 text-sm" lang={c.language === "Hindi" ? "hi" : undefined}>
          {c.text}
        </p>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
          <span>
            <b className="font-semibold text-foreground">{cur.category}</b> → <b className="font-semibold text-foreground">{cur.department}</b>
            {!cur.decided && <span> ({pct(c.ai.department_confidence)} sure)</span>}
          </span>
          <span>
            ~{days(cur.expected_days)} to resolve · SLA {cur.sla_days} d
          </span>
          <SlaFlag risk={cur.sla_breach_risk && !closed} breached={cur.sla_breached && !closed} />
          {c.top_words.length > 0 && (
            <span className="flex flex-wrap items-center gap-1">
              key words:
              {c.top_words.map((w) => (
                <Badge key={w} tone="violet">
                  {w}
                </Badge>
              ))}
            </span>
          )}
        </div>
      </div>
      <ChevronRight className="size-5 shrink-0 text-muted-foreground" aria-hidden />
    </Link>
  );
}

export default function Queue() {
  const [status, setStatus] = useState<Status>("Submitted");
  const [department, setDepartment] = useState(ALL);
  const [priority, setPriority] = useState(ALL);
  const [search, setSearch] = useState("");
  const q = useDebounced(search.trim());
  const meta = useMeta();
  const queue = useQueue({ status, department: department === ALL ? "" : department, priority: priority === ALL ? "" : priority, q });
  const data = queue.data;
  const filtering = department !== ALL || priority !== ALL || q !== "";

  return (
    <div>
      <PageHeader
        title="Triage queue"
        description="AI suggestions are ranked by priority. Open a complaint to review the reasons and decide."
        actions={
          <Button variant="secondary" magnetic={false} onClick={() => queue.refetch()} loading={queue.isFetching}>
            {!queue.isFetching && <RefreshCw />} Refresh
          </Button>
        }
      />

      <Tabs
        value={status}
        onValueChange={(v) => setStatus(v as Status)}
        tabs={TABS.map((t) => ({ value: t.value, label: t.label, count: data?.counts?.[t.value] }))}
      >
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <SearchField className="w-full sm:w-72" value={search} onChange={setSearch} placeholder="Search text or tracking ID" label="Search complaints" />
          <Select
            className="w-full sm:w-52"
            aria-label="Department"
            value={department}
            onValueChange={setDepartment}
            options={[{ value: ALL, label: "All departments" }, ...(meta.data?.departments.map((d) => ({ value: d.name, label: d.name })) ?? [])]}
          />
          <Select
            className="w-full sm:w-44"
            aria-label="Priority"
            value={priority}
            onValueChange={setPriority}
            options={[{ value: ALL, label: "All priorities" }, ...PRIORITIES.map((p) => ({ value: p, label: p }))]}
          />
          {filtering && (
            <Button
              variant="ghost"
              size="sm"
              magnetic={false}
              onClick={() => {
                setDepartment(ALL);
                setPriority(ALL);
                setSearch("");
              }}
            >
              Clear filters
            </Button>
          )}
        </div>

        <TabPanel value={status} className="mt-4">
          <div aria-live="polite" className={cn("transition-opacity", queue.isFetching && data && "opacity-70")}>
            {queue.isPending ? (
              <div className="space-y-3" role="status" aria-label="Loading the queue">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="glass space-y-3 rounded-2xl p-4">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-3 w-2/3" />
                  </div>
                ))}
              </div>
            ) : queue.isError && !data ? (
              <ErrorState error={queue.error} title="Couldn't load the queue" hint="The list refreshes by itself every 20 seconds once the server answers." onRetry={() => queue.refetch()} />
            ) : data && data.items.length === 0 ? (
              <EmptyState
                icon={<Inbox />}
                title={filtering ? "No complaints match these filters" : status === "Submitted" ? "Nothing waiting for review" : `No ${status.toLowerCase()} complaints`}
                description={
                  filtering
                    ? "Try a different department, priority or search text."
                    : status === "Submitted"
                      ? "New complaints appear here as citizens file them."
                      : "Complaints move here as officers update their status."
                }
                action={
                  filtering ? (
                    <Button
                      variant="secondary"
                      magnetic={false}
                      onClick={() => {
                        setDepartment(ALL);
                        setPriority(ALL);
                        setSearch("");
                      }}
                    >
                      Clear filters
                    </Button>
                  ) : status !== "Submitted" ? (
                    <Button variant="secondary" magnetic={false} onClick={() => setStatus("Submitted")}>
                      Go to awaiting review
                    </Button>
                  ) : undefined
                }
              />
            ) : data ? (
              <>
                <Stagger className="space-y-3" gap={0.03} key={`${status}-${department}-${priority}-${q}`}>
                  {data.items.map((c) => (
                    <StaggerItem key={c.id}>
                      <Row c={c} status={status} />
                    </StaggerItem>
                  ))}
                </Stagger>
                {data.total > data.items.length && (
                  <p className="mt-3 text-xs text-muted-foreground">
                    Showing the first {data.items.length} of {data.total}. Use the filters to narrow down.
                  </p>
                )}
              </>
            ) : null}
          </div>
        </TabPanel>
      </Tabs>
    </div>
  );
}

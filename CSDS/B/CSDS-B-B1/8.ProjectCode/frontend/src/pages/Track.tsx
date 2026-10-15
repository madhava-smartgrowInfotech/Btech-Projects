import { Building2, CalendarClock, Circle, FilePlus2, MapPin, MessageSquare, Search } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { SampleBadge, StatusBadge } from "@/components/domain/Badges";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Timeline } from "@/components/ui/Display";
import { Input } from "@/components/ui/Field";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { fmtDate, fmtDay } from "@/lib/format";
import { useMyComplaints, useTracked } from "@/lib/queries";
import type { CitizenComplaint } from "@/lib/types";
import { cn } from "@/lib/utils";

function Fact({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 text-muted-foreground [&_svg]:size-4">{icon}</span>
      <div>
        <dt className="text-xs text-muted-foreground">{label}</dt>
        <dd className="text-sm font-medium">{value}</dd>
      </div>
    </div>
  );
}

function Detail({ c }: { c: CitizenComplaint }) {
  useBreadcrumb(c.tracking_id);
  return (
    <Card strong>
      <CardBody className="space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-lg font-semibold">{c.tracking_id}</span>
          <StatusBadge status={c.status} />
          <SampleBadge show={c.is_sample} />
        </div>
        <p className="whitespace-pre-line text-sm leading-relaxed">{c.text}</p>
        {c.photo_url && <img src={c.photo_url} alt="Photo attached to the complaint" className="max-h-56 rounded-xl border border-[var(--glass-border)]" />}
        <dl className="grid gap-4 sm:grid-cols-3">
          <Fact icon={<Building2 />} label="Department" value={c.department || "Under review"} />
          <Fact
            icon={<CalendarClock />}
            label={c.status === "Resolved" ? "Resolved on" : "Expected by"}
            value={c.status === "Resolved" ? fmtDay(c.resolved_at) : c.expected_by ? fmtDay(c.expected_by) : "After review"}
          />
          <Fact icon={<MapPin />} label="Ward" value={c.ward || "Not pinned"} />
        </dl>
        <div>
          <h3 className="mb-3 font-display text-sm font-semibold">Progress</h3>
          <Timeline
            items={c.timeline.map((e) => ({
              icon: e.kind === "reply" ? <MessageSquare /> : <Circle />,
              title: e.kind === "reply" ? "Reply from the grievance cell" : <StatusBadge status={e.status} />,
              meta: fmtDate(e.at),
              body: e.message ? <span className="whitespace-pre-line text-foreground/80">{e.message}</span> : undefined,
            }))}
          />
        </div>
      </CardBody>
    </Card>
  );
}

export default function Track() {
  const { trackingId } = useParams();
  const navigate = useNavigate();
  const list = useMyComplaints();
  const tracked = useTracked(trackingId);
  const [search, setSearch] = useState(trackingId ?? "");

  useEffect(() => setSearch(trackingId ?? ""), [trackingId]);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    if (search.trim()) navigate(`/app/track/${search.trim().toUpperCase()}`);
  }

  return (
    <div>
      <PageHeader
        title="My complaints"
        description="Status updates and replies from the grievance cell appear here, refreshed every 20 seconds."
        actions={
          <form onSubmit={onSearch} className="flex gap-2" role="search">
            <Input
              aria-label="Tracking ID"
              placeholder="CP-2609-00001"
              className="font-mono"
              wrapperClassName="w-48"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Button type="submit" variant="secondary" magnetic={false}>
              <Search /> Track
            </Button>
          </form>
        }
      />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <section aria-label="Your complaints" className="space-y-2">
          {list.isPending ? (
            <div className="space-y-2" role="status" aria-label="Loading your complaints">
              {[0, 1, 2].map((i) => (
                <div key={i} className="glass space-y-2 rounded-2xl p-4">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
              ))}
            </div>
          ) : list.isError ? (
            <ErrorState error={list.error} title="Couldn't load your complaints" hint="Your complaints are safe - check the connection and try again." onRetry={() => list.refetch()} />
          ) : list.data.length === 0 ? (
            <EmptyState
              icon={<FilePlus2 />}
              title="No complaints yet"
              description="File your first complaint and it will show up here with a live status timeline."
              action={
                <Button asChild>
                  <Link to="/app/file">
                    <FilePlus2 /> File a complaint
                  </Link>
                </Button>
              }
            />
          ) : (
            <Stagger className="space-y-2" gap={0.04}>
              {list.data.map((c) => (
                <StaggerItem key={c.id}>
                  <Link
                    to={`/app/track/${c.tracking_id}`}
                    aria-current={trackingId === c.tracking_id ? "true" : undefined}
                    className={cn(
                      "glass sweep block rounded-2xl p-4 transition-[transform,border-color] hover:-translate-y-0.5 hover:border-[color-mix(in_srgb,var(--violet)_40%,var(--glass-border))]",
                      trackingId === c.tracking_id && "border-[var(--violet)] ring-2 ring-[color-mix(in_srgb,var(--violet)_30%,transparent)]",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-sm font-semibold">{c.tracking_id}</span>
                      <StatusBadge status={c.status} />
                    </div>
                    <p className="mt-1.5 line-clamp-2 text-sm text-muted-foreground">{c.text}</p>
                    <div className="mt-2 text-xs text-muted-foreground">{fmtDate(c.created_at)}</div>
                  </Link>
                </StaggerItem>
              ))}
            </Stagger>
          )}
        </section>

        <section aria-label="Complaint progress" aria-live="polite">
          {!trackingId ? (
            <EmptyState icon={<Search />} title="Select a complaint" description="Pick one from the list, or search by tracking ID, to see its progress." />
          ) : tracked.isPending ? (
            <Card>
              <CardHeader title="Loading complaint…" />
              <CardBody className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-24 w-full" />
              </CardBody>
            </Card>
          ) : tracked.isError ? (
            <ErrorState error={tracked.error} title="Couldn't open that complaint" hint="Check the tracking ID - it looks like CP-2609-00001." onRetry={() => tracked.refetch()} />
          ) : (
            <Detail c={tracked.data} />
          )}
        </section>
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { Accessibility, ArrowRight, CalendarClock, FileText, Upload, Users } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/States";
import { PlanStatusBadge } from "@/components/plans/PlanStatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { ExamSession } from "@/lib/types";

export default function SessionsPage() {
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: async () => (await api.get<ExamSession[]>("/sessions")).data });

  return (
    <>
      <PageHeader
        title="Sittings & plans"
        description="Each sitting from the timetable gets its own seating plan. Generate, review and publish them here."
      />
      {sessions.isPending && <TableSkeleton rows={5} />}
      {sessions.isError && <ErrorState error={sessions.error} onRetry={() => sessions.refetch()} />}
      {sessions.data?.length === 0 && (
        <EmptyState
          icon={CalendarClock}
          title="No sittings yet"
          description="Import a timetable to create sittings, then plan the seating for each."
          action={
            <Button asChild>
              <Link to="/app/import">
                <Upload /> Import data
              </Link>
            </Button>
          }
        />
      )}
      <div className="grid gap-3">
        {sessions.data?.map((s, i) => {
          const status = s.plans.published_id ? "published" : s.plans.latest_status;
          return (
            <motion.div key={s.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.04, 0.3) }}>
              <Card className="transition-shadow hover:shadow-lift">
                <CardContent className="flex flex-col gap-4 p-4 sm:p-5 md:flex-row md:items-center">
                  <div className="flex size-14 shrink-0 flex-col items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <span className="text-2xs font-semibold uppercase">{formatDate(s.date).split(" ")[0]}</span>
                    <span className="font-display text-xl font-semibold leading-none">{s.start_time}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{s.label}</span>
                      <PlanStatusBadge status={status} />
                    </div>
                    <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
                      <span className="inline-flex items-center gap-1.5">
                        <Users className="size-4" /> {formatNumber(s.candidates)} candidates
                      </span>
                      <span className="inline-flex items-center gap-1.5">
                        <FileText className="size-4" /> {s.papers.length} papers
                      </span>
                      {s.accessible_candidates > 0 && (
                        <span className="inline-flex items-center gap-1.5">
                          <Accessibility className="size-4" /> {s.accessible_candidates} need accessible seats
                        </span>
                      )}
                      <span>{s.start_time}-{s.end_time}</span>
                    </div>
                  </div>
                  <Button asChild variant={s.plans.count ? "outline" : "default"} className="shrink-0">
                    <Link to={`/app/sessions/${s.id}`}>
                      {s.plans.count ? "Open" : "Plan seating"} <ArrowRight />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </>
  );
}

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ArrowRight, CheckCircle2, ClipboardCheck, Lock } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import type { AttendanceAssignment } from "@/lib/types";

function Bar({ a }: { a: AttendanceAssignment }) {
  const pct = (n: number) => `${a.total ? (n / a.total) * 100 : 0}%`;
  return (
    <div className="flex h-2 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
      <span className="bg-success transition-all" style={{ width: pct(a.present) }} />
      <span className="bg-destructive transition-all" style={{ width: pct(a.absent) }} />
    </div>
  );
}

export default function AttendancePage() {
  const { user } = useAuth();
  const list = useQuery({
    queryKey: ["attendance", "assignments"],
    queryFn: async () => (await api.get<AttendanceAssignment[]>("/attendance/assignments")).data,
    refetchInterval: 10_000,
  });

  const groups = new Map<string, AttendanceAssignment[]>();
  for (const a of list.data ?? []) {
    const key = `${a.session.date} ${a.session.start_time}`;
    groups.set(key, [...(groups.get(key) ?? []), a]);
  }

  return (
    <>
      <PageHeader
        title={user?.role === "admin" ? "Attendance" : "My halls"}
        description={
          user?.role === "admin"
            ? "Live attendance in every hall of every published plan."
            : "The halls you supervise. Mark each candidate present or absent, then submit the register."
        }
      />
      {list.isPending && <TableSkeleton rows={4} />}
      {list.isError && <ErrorState error={list.error} onRetry={() => list.refetch()} />}
      {list.data?.length === 0 && (
        <EmptyState
          icon={ClipboardCheck}
          title={user?.role === "admin" ? "No published plans yet" : "No halls assigned to you yet"}
          description={
            user?.role === "admin"
              ? "Attendance opens once a sitting's plan is published."
              : "Your halls appear here as soon as the exam controller publishes a plan with you as invigilator."
          }
        />
      )}
      <div className="space-y-8">
        {[...groups.entries()].map(([key, items]) => (
          <section key={key}>
            <h2 className="mb-3 text-sm font-semibold">
              {items[0].session.label}
              <span className="ml-2 font-normal text-muted-foreground">
                {formatDate(items[0].session.date)} · {items[0].session.start_time}-{items[0].session.end_time}
              </span>
            </h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((a, i) => (
                <motion.div key={`${a.plan_id}-${a.hall.id}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                  <Card className={a.mine ? "border-primary/50" : undefined}>
                    <CardContent className="space-y-3 p-4">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="font-mono text-xs text-muted-foreground">{a.hall.code}</div>
                          <div className="font-semibold">{a.hall.name}</div>
                          <div className="text-xs text-muted-foreground">{a.invigilators.join(", ") || "No invigilator"}</div>
                        </div>
                        {a.submitted_at ? (
                          <Badge variant="success"><Lock /> Submitted</Badge>
                        ) : a.present + a.absent > 0 ? (
                          <Badge>In progress</Badge>
                        ) : (
                          <Badge variant="outline">Not started</Badge>
                        )}
                      </div>
                      <Bar a={a} />
                      <div className="flex justify-between text-xs tabular text-muted-foreground">
                        <span className="text-success">{a.present} present</span>
                        <span className="text-destructive">{a.absent} absent</span>
                        <span>{a.unmarked} to mark</span>
                      </div>
                      <Button asChild className="w-full" variant={a.submitted_at ? "outline" : "default"}>
                        <Link to={`/app/attendance/${a.plan_id}/${a.hall.id}`}>
                          {a.submitted_at ? <CheckCircle2 /> : null}
                          {a.submitted_at ? "View register" : "Take attendance"} <ArrowRight />
                        </Link>
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}

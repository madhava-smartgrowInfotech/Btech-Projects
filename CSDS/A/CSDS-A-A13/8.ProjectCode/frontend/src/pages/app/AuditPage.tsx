import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeftRight, CheckCircle2, FileSearch, Globe, ScrollText, Settings, Sparkles, Trash2, Upload, UserCog, XCircle,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/States";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { AuditEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

const FILTERS = [
  { value: "", label: "Everything" },
  { value: "plan.generated", label: "Plans made" },
  { value: "plan.seat_moved", label: "Seat moves" },
  { value: "plan.published", label: "Publishing" },
  { value: "plan.verified", label: "Verifications" },
  { value: "import", label: "Imports" },
  { value: "attendance", label: "Attendance" },
];

const ICONS: Record<string, LucideIcon> = {
  "plan.generated": Sparkles,
  "plan.failed": XCircle,
  "plan.published": Globe,
  "plan.verified": FileSearch,
  "plan.seat_moved": ArrowLeftRight,
  "plan.deleted": Trash2,
  "import.committed": Upload,
  "settings.rules": Settings,
};

function iconFor(action: string) {
  return ICONS[action] ?? (action.startsWith("user") ? UserCog : action.startsWith("attendance") ? CheckCircle2 : ScrollText);
}

export default function AuditPage() {
  const [params, setParams] = useSearchParams();
  const planId = params.get("plan");
  const [filter, setFilter] = useState("");
  const events = useQuery({
    queryKey: ["audit", filter, planId],
    queryFn: async () =>
      (await api.get<AuditEvent[]>("/audit", { params: { action: filter || undefined, plan_id: planId || undefined, limit: 300 } })).data,
  });

  return (
    <>
      <PageHeader
        title="Audit trail"
        description="Every plan, seed, manual seat move, publication and import is recorded here and cannot be edited."
      />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => (
          <Button key={f.value} size="sm" variant={filter === f.value ? "secondary" : "ghost"} onClick={() => setFilter(f.value)}>
            {f.label}
          </Button>
        ))}
        {planId && (
          <Badge variant="outline" className="ml-auto">
            Plan #{planId}
            <button className="ml-1 text-muted-foreground hover:text-foreground" onClick={() => setParams({})} aria-label="Show all plans">
              ×
            </button>
          </Badge>
        )}
      </div>
      {events.isPending && <TableSkeleton />}
      {events.isError && <ErrorState error={events.error} onRetry={() => events.refetch()} />}
      {events.data?.length === 0 && <EmptyState icon={ScrollText} title="Nothing recorded yet" description="Actions appear here as soon as they happen." />}
      {events.data && events.data.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <ol className="divide-y">
              {events.data.map((e) => {
                const Icon = iconFor(e.action);
                const seed = typeof e.details.seed === "number" ? e.details.seed : null;
                return (
                  <li key={e.id} className="flex gap-3 p-4">
                    <span
                      className={cn(
                        "flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary",
                        e.action === "plan.failed" && "bg-destructive/10 text-destructive",
                      )}
                    >
                      <Icon className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">{e.summary}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        <span>{formatDateTime(e.at)}</span>
                        <span className="font-mono">{e.action}</span>
                        {seed !== null && <span className="font-mono">seed {seed}</span>}
                        {e.plan_id && (
                          <Link to={`/app/audit?plan=${e.plan_id}`} className="text-primary hover:underline">
                            plan #{e.plan_id}
                          </Link>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
          </CardContent>
        </Card>
      )}
    </>
  );
}

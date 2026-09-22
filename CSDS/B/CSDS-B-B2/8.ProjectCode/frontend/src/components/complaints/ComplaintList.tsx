import { Link } from "react-router-dom";
import { ChevronRight, RotateCcw, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Complaint } from "@/lib/complaints";
import { formatDateTime, timeAgo } from "@/lib/utils";
import { SeverityBadge, StatusBadge } from "./parts";

function age(c: Complaint) {
  const since = c.registered_at ?? c.detected_at;
  return timeAgo(since);
}

export function ComplaintList({ items, showAssignee = false }: { items: Complaint[]; showAssignee?: boolean }) {
  return (
    <ul className="divide-y overflow-hidden rounded-xl border bg-card">
      {items.map((c) => (
        <li key={c.id}>
          <Link to={`/app/complaints/${c.id}`} className="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-accent/50 focus-visible:bg-accent">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm font-semibold">{c.ref_code}</span>
                <StatusBadge status={c.status} />
                <SeverityBadge severity={c.severity} />
                {c.source === "sample_dataset" && <Badge variant="secondary">Sample</Badge>}
                {c.origin === "user" && <Badge variant="outline">User report</Badge>}
                {c.reopen_count > 0 && (
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground"><RotateCcw className="h-3 w-3" /> reopened</span>
                )}
              </div>
              <p className="mt-1 truncate text-sm text-muted-foreground">
                <span className="font-medium text-foreground">{c.operator}</span> · {c.readings.toLocaleString()} readings
                {c.bad_share != null && ` · ${Math.round(c.bad_share * 100)}% weak or dead`} · {c.lat.toFixed(4)}, {c.lon.toFixed(4)}
              </p>
            </div>
            <div className="hidden shrink-0 text-right text-xs text-muted-foreground sm:block">
              <p title={formatDateTime(c.registered_at ?? c.detected_at)}>{c.registered_at ? "Registered" : "Detected"} {age(c)}</p>
              {showAssignee && (
                <p className="mt-0.5 inline-flex items-center gap-1">
                  <UserRound className="h-3 w-3" /> {c.assigned_to_name ?? "Unassigned"}
                </p>
              )}
            </div>
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden />
          </Link>
        </li>
      ))}
    </ul>
  );
}

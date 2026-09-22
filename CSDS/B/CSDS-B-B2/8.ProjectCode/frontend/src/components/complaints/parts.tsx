import { Check, RotateCcw, X } from "lucide-react";
import { LIFECYCLE, STATUS_LABEL, STATUS_STYLE, type Complaint, type ComplaintStatus } from "@/lib/complaints";
import { cn, formatDateTime } from "@/lib/utils";

export function StatusBadge({ status, className }: { status: ComplaintStatus; className?: string }) {
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", STATUS_STYLE[status], className)}>{STATUS_LABEL[status]}</span>;
}

export function SeverityBadge({ severity }: { severity: "weak" | "dead" }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", severity === "dead" ? "bg-zone-dead/15 text-zone-dead" : "bg-zone-weak/15 text-[#8a5a00] dark:text-zone-weak")}>
      <span className={cn("h-1.5 w-1.5 rounded-full", severity === "dead" ? "bg-zone-dead" : "bg-zone-weak")} aria-hidden />
      {severity === "dead" ? "Dead zone" : "Weak zone"}
    </span>
  );
}

const STAMP: Record<ComplaintStatus, keyof Complaint> = {
  detected: "detected_at", registered: "registered_at", acknowledged: "acknowledged_at", in_progress: "in_progress_at",
  resolved: "resolved_at", verified: "verified_at", dismissed: "dismissed_at",
};

/** Horizontal lifecycle with the time each step was reached. */
export function StatusStepper({ c }: { c: Complaint }) {
  const current = c.status === "dismissed" ? -1 : LIFECYCLE.indexOf(c.status);
  return (
    <div className="overflow-x-auto pb-1">
      <ol className="flex min-w-[560px] items-start">
        {LIFECYCLE.map((s, i) => {
          const at = c[STAMP[s]] as string | null;
          const done = current >= 0 ? i <= current : Boolean(at);
          const active = i === current;
          return (
            <li key={s} className="flex flex-1 flex-col items-center text-center">
              <div className="flex w-full items-center">
                <span className={cn("h-0.5 flex-1", i === 0 ? "invisible" : done ? "bg-primary" : "bg-border")} />
                <span className={cn("flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold",
                  done ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground", active && "ring-4 ring-primary/20")}>
                  {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
                </span>
                <span className={cn("h-0.5 flex-1", i === LIFECYCLE.length - 1 ? "invisible" : done && i < current ? "bg-primary" : "bg-border")} />
              </div>
              <p className={cn("mt-1.5 text-xs font-medium", active ? "text-foreground" : "text-muted-foreground")}>{STATUS_LABEL[s]}</p>
              <p className="text-[10px] text-muted-foreground">{at ? formatDateTime(at) : ""}</p>
            </li>
          );
        })}
      </ol>
      {c.status === "dismissed" && <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground"><X className="h-3.5 w-3.5" /> Dismissed {formatDateTime(c.dismissed_at)}</p>}
      {c.reopen_count > 0 && <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground"><RotateCcw className="h-3.5 w-3.5" /> Reopened {c.reopen_count} time{c.reopen_count > 1 ? "s" : ""} after a fix did not hold</p>}
    </div>
  );
}

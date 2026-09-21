import { CheckCircle2, CircleHelp, ShieldAlert, ShieldCheck, ShieldX, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { CheckStatus, DocStatus, Severity, Verdict } from "@/lib/types";
import { cn } from "@/lib/utils";

const severityStyles: Record<Severity, string> = {
  high: "border-destructive/30 bg-destructive/10 text-destructive",
  medium: "border-warning/40 bg-warning/15 text-warning-foreground dark:text-warning",
  low: "border-info/30 bg-info/10 text-info",
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  return (
    <Badge variant="outline" className={cn("capitalize", severityStyles[severity], className)}>
      {severity}
    </Badge>
  );
}

const statusLabels: Record<DocStatus, string> = {
  queued: "Queued",
  parsing: "Reading PDF",
  indexing: "Indexing",
  extracting: "Building card",
  ready: "Ready",
  failed: "Failed",
};

export function DocStatusBadge({ status }: { status: DocStatus }) {
  const style =
    status === "ready"
      ? "border-success/30 bg-success/10 text-success"
      : status === "failed"
        ? severityStyles.high
        : "border-primary/30 bg-primary/10 text-primary";
  return (
    <Badge variant="outline" className={style}>
      {status !== "ready" && status !== "failed" && <span className="size-1.5 animate-pulse rounded-full bg-current" />}
      {statusLabels[status]}
    </Badge>
  );
}

export const verdictMeta: Record<Verdict, { label: string; icon: typeof ShieldCheck; tone: string; bar: string }> = {
  covered: { label: "Covered", icon: ShieldCheck, tone: "text-success", bar: "bg-success" },
  partly_covered: { label: "Partly covered", icon: ShieldAlert, tone: "text-warning-foreground dark:text-warning", bar: "bg-warning" },
  not_covered: { label: "Not covered", icon: ShieldX, tone: "text-destructive", bar: "bg-destructive" },
  needs_info: { label: "Needs more information", icon: CircleHelp, tone: "text-info", bar: "bg-info" },
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const meta = verdictMeta[verdict];
  const Icon = meta.icon;
  return (
    <Badge variant="outline" className={cn("gap-1", meta.tone)}>
      <Icon className="size-3.5" />
      {meta.label}
    </Badge>
  );
}

export function CheckStatusIcon({ status }: { status: CheckStatus }) {
  if (status === "pass") return <CheckCircle2 className="size-4 text-success" aria-label="Pass" />;
  if (status === "fail") return <ShieldX className="size-4 text-destructive" aria-label="Fails" />;
  if (status === "warning") return <TriangleAlert className="size-4 text-warning" aria-label="Check" />;
  return <CircleHelp className="size-4 text-muted-foreground" aria-label="Unknown" />;
}

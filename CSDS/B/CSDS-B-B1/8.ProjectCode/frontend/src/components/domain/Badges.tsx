import { AlertTriangle, ArrowDown, ArrowUp, CheckCircle2, Clock, Flame, Loader2, Minus, UserCheck, XCircle, type LucideIcon } from "lucide-react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Tooltip } from "@/components/ui/Popups";
import type { Priority, Status } from "@/lib/types";

/* Colour is never the only signal: every badge also carries an icon and its label. */
const PRIORITY: Record<Priority, { tone: BadgeTone; icon: LucideIcon }> = {
  Low: { tone: "neutral", icon: ArrowDown },
  Medium: { tone: "info", icon: Minus },
  High: { tone: "warning", icon: ArrowUp },
  Critical: { tone: "danger", icon: Flame },
};

export const PRIORITY_COLOR: Record<Priority, string> = {
  Low: "#94A3B8",
  Medium: "#38BDF8",
  High: "#FBBF24",
  Critical: "#FB7185",
};

export function PriorityBadge({ priority }: { priority: Priority | null | undefined }) {
  if (!priority) return null;
  const { tone, icon: Icon } = PRIORITY[priority];
  return (
    <Badge tone={tone}>
      <Icon aria-hidden /> {priority}
    </Badge>
  );
}

const STATUS: Record<Status, { tone: BadgeTone; icon: LucideIcon; spin?: boolean }> = {
  Submitted: { tone: "neutral", icon: Clock },
  Assigned: { tone: "violet", icon: UserCheck },
  "In Progress": { tone: "warning", icon: Loader2 },
  Resolved: { tone: "success", icon: CheckCircle2 },
  Rejected: { tone: "neutral", icon: XCircle },
};

export function StatusBadge({ status }: { status: Status | null | undefined }) {
  if (!status) return null;
  const { tone, icon: Icon } = STATUS[status] ?? STATUS.Submitted;
  return (
    <Badge tone={tone}>
      <Icon aria-hidden /> {status}
    </Badge>
  );
}

export function SampleBadge({ show }: { show?: boolean }) {
  if (!show) return null;
  return (
    <Tooltip content="Sample data generated for demonstration">
      <span tabIndex={0} className="inline-flex rounded-full">
        <Badge tone="neutral" className="uppercase tracking-wide">
          Sample
        </Badge>
      </span>
    </Tooltip>
  );
}

export function SlaFlag({ risk, breached }: { risk?: boolean; breached?: boolean }) {
  if (!risk && !breached) return null;
  return (
    <Tooltip content={breached ? "Open longer than the department SLA" : "Expected time is longer than the department SLA"}>
      <span tabIndex={0} className="inline-flex rounded-full">
        <Badge tone={breached ? "danger" : "warning"}>
          <AlertTriangle aria-hidden /> {breached ? "SLA breached" : "SLA risk"}
        </Badge>
      </span>
    </Tooltip>
  );
}

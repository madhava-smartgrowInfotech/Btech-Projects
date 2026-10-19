import { Check, Copy, ShieldAlert, ShieldCheck } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import type { AuditEntry, ChainStatus, ElectionStatus, Validator } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const STATUS_TONE: Record<ElectionStatus, BadgeTone> = {
  OPEN: "success",
  PAUSED: "warning",
  CLOSED: "neutral",
  DRAFT: "info",
};
const STATUS_LABEL: Record<ElectionStatus, string> = { OPEN: "Open", PAUSED: "Paused", CLOSED: "Closed", DRAFT: "Draft" };

export function StatusBadge({ status }: { status: ElectionStatus }) {
  return (
    <Badge tone={STATUS_TONE[status] ?? "neutral"}>
      <span className={cn("size-1.5 rounded-full bg-current", status === "OPEN" && "animate-pulse")} aria-hidden />
      {STATUS_LABEL[status] ?? status}
    </Badge>
  );
}

/** Monospace hash, shortened in the UI, with a copy button that copies the full value. */
export function Hash({ value, head = 10, tail = 6, className }: { value: string; head?: number; tail?: number; className?: string }) {
  const [copied, setCopied] = useState(false);
  const short = value.length > head + tail + 1 ? `${value.slice(0, head)}…${value.slice(-tail)}` : value;
  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Could not copy. Select the text and copy it manually.");
    }
  }
  return (
    <span className={cn("inline-flex max-w-full items-center gap-1 align-middle", className)}>
      <code className="truncate font-mono text-xs" title={value}>
        {short}
      </code>
      <button
        type="button"
        onClick={copy}
        aria-label="Copy full value"
        className="grid size-6 shrink-0 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
      </button>
    </span>
  );
}

/** Full-width hash block for detail pages (wraps instead of truncating). */
export function HashBlock({ value }: { value: string }) {
  return <code className="block break-all rounded-lg bg-muted px-2.5 py-2 font-mono text-xs leading-relaxed">{value}</code>;
}

export function ChainBadge({ chain }: { chain: ChainStatus }) {
  return chain.valid ? (
    <Badge tone="success">
      <ShieldCheck /> Ledger healthy
    </Badge>
  ) : (
    <Badge tone="danger">
      <ShieldAlert /> Integrity warning
    </Badge>
  );
}

export function ValidatorList({ validators }: { validators: Validator[] }) {
  return (
    <ul className="divide-y divide-[var(--glass-border)]">
      {validators.map((v) => (
        <li key={v.node_id} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0">
            <div className="text-sm font-medium">{v.node_id}</div>
            <Hash value={v.public_key} head={12} tail={6} className="text-muted-foreground" />
          </div>
          <Badge tone={v.is_active ? "success" : "neutral"}>{v.is_active ? "Active" : "Inactive"}</Badge>
        </li>
      ))}
    </ul>
  );
}

export function AuditTable({ logs, pageSize = 8, empty }: { logs: AuditEntry[]; pageSize?: number; empty?: ReactNode }) {
  const columns: Column<AuditEntry>[] = [
    { key: "time", header: "Time", cell: (l) => <span className="whitespace-nowrap text-xs text-muted-foreground">{formatDate(l.timestamp, true)}</span>, sortValue: (l) => l.id },
    { key: "actor", header: "Actor", cell: (l) => l.actor ?? "anonymous" },
    { key: "action", header: "Action", cell: (l) => <Badge tone={l.action.includes("fail") || l.action.includes("reject") ? "danger" : "neutral"}>{l.action}</Badge> },
    { key: "details", header: "Details", cell: (l) => <span className="line-clamp-2 break-all text-xs text-muted-foreground">{l.details ?? ""}</span>, hideOnCard: false },
  ];
  return <Table columns={columns} rows={logs} rowKey={(l) => l.id} pageSize={pageSize} initialSort={{ key: "time", dir: "desc" }} caption="Audit log" empty={empty} />;
}

export function formatPct(n: number | null | undefined) {
  return n === null || n === undefined ? "-" : `${n.toFixed(1)}%`;
}

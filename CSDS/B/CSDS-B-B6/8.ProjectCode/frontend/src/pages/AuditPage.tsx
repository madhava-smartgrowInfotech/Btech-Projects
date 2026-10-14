import { useQuery } from "@tanstack/react-query";
import { ScrollText, ShieldAlert, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { SearchField } from "@/components/ui/Field";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { type Column, Table } from "@/components/ui/Table";
import { api } from "@/lib/api";
import { useAuth, type Role } from "@/lib/auth";
import { keys } from "@/lib/queries";
import type { AuditEntry, AuditLog } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const SCOPE: Record<Role, string> = {
  patient: "Everything that happened to your record",
  doctor: "Your own actions",
  staff: "Your own actions",
  admin: "All platform events",
};

function actionTone(action: string): BadgeTone {
  if (action.startsWith("access.denied")) return "danger";
  if (action.startsWith("consent")) return "violet";
  if (action.startsWith("record") || action.startsWith("risk")) return "info";
  if (action.startsWith("assistant")) return "cyan";
  if (action.startsWith("sync") || action.startsWith("hospital")) return "success";
  return "neutral";
}

/** "key: value" pairs from an entry's detail, with empty values dropped. */
function detailText(detail: Record<string, unknown>): string {
  return Object.entries(detail)
    .filter(([, v]) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0))
    .map(([k, v]) => {
      const text = Array.isArray(v) ? v.join(", ") : typeof v === "object" ? JSON.stringify(v) : String(v).slice(0, 40);
      return `${k}: ${text}`;
    })
    .join(" · ");
}

/** The hash-chained ledger: who did what, with a live tamper check. */
export default function AuditPage() {
  const { user } = useAuth();
  const audit = useQuery({ queryKey: keys.audit, queryFn: async () => (await api.get<AuditLog>("/audit")).data });
  const [filter, setFilter] = useState("");

  const verification = audit.data?.verification;
  const entries = useMemo(
    () =>
      (audit.data?.entries ?? []).filter(
        (e) => !filter || `${e.action} ${e.actor} ${e.person_id ?? ""}`.toLowerCase().includes(filter.trim().toLowerCase()),
      ),
    [audit.data, filter],
  );

  const columns: Column<AuditEntry>[] = [
    { key: "id", header: "#", cell: (e) => <span className="text-muted-foreground">{e.id}</span>, sortValue: (e) => e.id, hideOnCard: true },
    { key: "ts", header: "Time", cell: (e) => <span className="whitespace-nowrap text-xs">{formatDate(e.ts, true)}</span>, sortValue: (e) => e.ts },
    { key: "actor", header: "Actor", cell: (e) => <span className="text-xs">{e.actor}</span>, sortValue: (e) => e.actor },
    {
      key: "action",
      header: "Action",
      cell: (e) => <Badge tone={actionTone(e.action)}>{e.action}</Badge>,
      sortValue: (e) => e.action,
    },
    { key: "person", header: "Person", cell: (e) => <span className="font-mono text-xs">{e.person_id ?? "-"}</span> },
    {
      key: "detail",
      header: "Detail",
      cell: (e) => <span className="block max-w-md text-xs text-muted-foreground">{detailText(e.detail) || "-"}</span>,
      className: "min-w-64",
    },
    {
      key: "hash",
      header: "Hash",
      cell: (e) => (
        <span className="font-mono text-xs text-muted-foreground" title={`previous ${e.prev_hash}`}>
          {e.hash.slice(0, 10)}
        </span>
      ),
      hideOnCard: true,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Accountability" title="Audit and consent log" description="Every access, consent change and sync is recorded in a hash-chained ledger." />

      {audit.isPending ? (
        <CardsSkeleton count={1} className="grid-cols-1" />
      ) : audit.isError ? (
        <ErrorState error={audit.error} onRetry={() => audit.refetch()} />
      ) : (
        verification && (
          <div
            role="status"
            className={cn(
              "glass flex flex-wrap items-center gap-4 rounded-2xl border p-4",
              verification.intact ? "border-success/35" : "border-danger/40",
            )}
          >
            {verification.intact ? (
              <ShieldCheck className="size-8 shrink-0 text-success" aria-hidden />
            ) : (
              <ShieldAlert className="size-8 shrink-0 text-danger" aria-hidden />
            )}
            <div className="min-w-0 flex-1">
              <div className={cn("font-display font-semibold", verification.intact ? "text-success" : "text-danger")}>
                {verification.intact ? "Ledger verified intact" : `Tampering detected at entry #${verification.broken_at}`}
              </div>
              <div className="text-xs text-muted-foreground">
                {verification.entries} hash-chained entries (SHA-256)
                {verification.intact && verification.head ? (
                  <>
                    {" "}
                    · head <span className="font-mono">{verification.head.slice(0, 16)}...</span>
                  </>
                ) : null}
              </div>
            </div>
            <Button variant="secondary" loading={audit.isFetching} onClick={() => audit.refetch()}>
              Verify again
            </Button>
          </div>
        )
      )}

      <Card>
        <CardHeader
          icon={<ScrollText />}
          title={user ? SCOPE[user.role] : "Audit entries"}
          action={
            <div className="w-full sm:w-64">
              <SearchField value={filter} onChange={setFilter} placeholder="Filter by action, actor or person" label="Filter audit entries" />
            </div>
          }
        />
        <CardBody>
          {audit.isPending ? null : (
            <Table
              caption="Audit entries"
              columns={columns}
              rows={entries}
              rowKey={(e) => e.id}
              pageSize={15}
              initialSort={{ key: "id", dir: "desc" }}
              empty={<EmptyState icon={<ScrollText />} title="No entries yet" description="Entries appear here as people sign in, request records and change consent." />}
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

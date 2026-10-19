import { Blocks, FlaskConical, ListTree, ScrollText, ShieldAlert, ShieldCheck, Users } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router";

import { AuditTable, ChainBadge, Hash, ValidatorList } from "@/components/domain/common";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useAuditorOverview, useTamperTest, useVerifyChain } from "@/lib/queries";
import type { Block, ChainStatus, TamperResult, Transaction } from "@/lib/types";
import { formatDate } from "@/lib/utils";

function ResultNote({ ok, title, children }: { ok: boolean; title: string; children: React.ReactNode }) {
  return (
    <div role="status" className={`rounded-xl border px-3 py-2.5 text-sm ${ok ? "border-success/30 bg-success/10" : "border-danger/30 bg-danger/10"}`}>
      <div className={`flex items-center gap-1.5 font-medium ${ok ? "text-success" : "text-danger"}`}>
        {ok ? <ShieldCheck className="size-4" /> : <ShieldAlert className="size-4" />} {title}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">{children}</div>
    </div>
  );
}

export default function AuditorDashboard() {
  const q = useAuditorOverview();
  const verify = useVerifyChain();
  const tamper = useTamperTest();
  const navigate = useNavigate();
  const [tab, setTab] = useState("blocks");
  const [verified, setVerified] = useState<ChainStatus | null>(null);
  const [tampered, setTampered] = useState<TamperResult | null>(null);

  async function runVerify() {
    try {
      const r = await verify.mutateAsync();
      setVerified(r);
      r.valid ? toast.success(`Ledger verified: ${r.height} blocks, no tampering found`) : toast.error(`Integrity failure at block ${r.first_invalid}`);
    } catch (err) {
      toast.error(errorMessage(err, "Verification could not run."));
    }
  }
  async function runTamper() {
    try {
      const r = await tamper.mutateAsync();
      setTampered(r);
      if (r.tested === false) toast.info(r.reason ?? "Not enough blocks to run the demo");
      else toast.success(r.detected ? "Tampering on the cloned ledger was detected" : "Tampering was not detected");
    } catch (err) {
      toast.error(errorMessage(err, "The tamper demo could not run."));
    }
  }

  const header = (
    <PageHeader
      eyebrow="Auditor"
      title="Ledger audit"
      description="Verify the chain from genesis, inspect any block and review the audit log. The tamper demo only touches an in-memory clone."
      actions={<Badge tone="warning">Tamper demo is safe: it uses a cloned copy</Badge>}
    />
  );

  if (q.isPending) return <>{header}<div className="space-y-4" role="status" aria-label="Loading audit data"><div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-64 rounded-2xl" /><Skeleton className="h-64 rounded-2xl" /></div><Skeleton className="h-80 rounded-2xl" /></div></>;
  if (q.isError) return <>{header}<ErrorState error={q.error} title="Could not load audit data" onRetry={() => q.refetch()} /></>;

  const d = q.data;
  const chain = verified ?? d.chain;

  const blockCols: Column<Block>[] = [
    { key: "i", header: "Block", cell: (b) => <span className="font-medium">#{b.block_index}</span>, sortValue: (b) => b.block_index },
    { key: "hash", header: "Hash", cell: (b) => <Hash value={b.block_hash} /> },
    { key: "prev", header: "Previous", cell: (b) => <Hash value={b.previous_hash} head={8} tail={4} />, hideOnCard: true },
    { key: "time", header: "Time", cell: (b) => <span className="whitespace-nowrap text-xs text-muted-foreground">{formatDate(b.timestamp, true)}</span>, hideOnCard: true },
    { key: "tx", header: "Tx", cell: (b) => b.transaction_count, align: "right" },
  ];
  const txCols: Column<Transaction>[] = [
    { key: "tx", header: "Tx hash", cell: (t) => <Hash value={t.tx_hash} /> },
    { key: "ballot", header: "Anonymous ballot", cell: (t) => <Hash value={t.ballot_id} head={10} tail={4} /> },
    { key: "block", header: "Block", cell: (t) => `#${t.block_index}`, align: "right" },
  ];

  return (
    <>
      {header}
      <Stagger className="space-y-4">
        <StaggerItem className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
          <Card>
            <CardHeader title="Chain integrity" icon={<ShieldCheck />} action={<ChainBadge chain={chain} />} />
            <CardBody className="space-y-4">
              {chain.valid ? (
                <div className="space-y-1">
                  <div className="font-display text-3xl font-semibold tabular-nums">{chain.height} <span className="text-base font-normal text-muted-foreground">blocks</span></div>
                  {chain.last_hash && <div className="flex items-center gap-2 text-xs text-muted-foreground">Tip <Hash value={chain.last_hash} head={16} tail={8} /></div>}
                </div>
              ) : (
                <ResultNote ok={false} title={`Invalid at block ${chain.first_invalid ?? "?"}`}>
                  {chain.field && <>Field <code className="font-mono">{chain.field}</code> does not match. </>}
                  {chain.expected && <>Expected <Hash value={chain.expected} head={10} tail={4} /> but found <Hash value={chain.actual ?? ""} head={10} tail={4} />.</>}
                  {chain.reason}
                </ResultNote>
              )}
              <div className="flex flex-wrap gap-2">
                <Button onClick={runVerify} loading={verify.isPending}><ShieldCheck /> Verify ledger integrity</Button>
                <Button variant="secondary" onClick={runTamper} loading={tamper.isPending}><FlaskConical /> Run tamper-detection demo</Button>
              </div>
              {verified && (
                <ResultNote ok={verified.valid} title={verified.valid ? "Verified just now" : "Verification failed"}>
                  Recomputed SHA-256 hashes and Merkle roots from genesis to tip{verified.valid ? `: all ${verified.height} blocks are consistent.` : "."}
                </ResultNote>
              )}
              {tampered && (
                tampered.tested === false ? (
                  <ResultNote ok={false} title="Demo could not run">{tampered.reason ?? "Not enough blocks."}</ResultNote>
                ) : (
                  <ResultNote ok={!!tampered.detected} title={tampered.detected ? "Tampering detected on the clone" : "Tampering was NOT detected"}>
                    <span className="block">Block {tampered.tampered_block} of a cloned ledger was altered. The production ledger is unchanged.</span>
                    {tampered.expected && tampered.tampered && (
                      <span className="mt-2 grid gap-1.5 sm:grid-cols-[auto_1fr] sm:items-center">
                        <span>Original hash</span><Hash value={tampered.expected} head={14} tail={6} />
                        <span>Tampered hash</span><Hash value={tampered.tampered} head={14} tail={6} />
                      </span>
                    )}
                  </ResultNote>
                )
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Validators" description="Quorum: 2 of 3 must approve each block" icon={<Users />} />
            <CardBody>
              {d.validators.length === 0 ? <p className="text-sm text-muted-foreground">No validator nodes registered.</p> : <ValidatorList validators={d.validators} />}
            </CardBody>
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Tabs
            value={tab}
            onValueChange={setTab}
            tabs={[
              { value: "blocks", label: "Blocks", icon: <Blocks />, count: d.blocks.length },
              { value: "txs", label: "Transactions", icon: <ListTree />, count: d.transactions.length },
              { value: "log", label: "Audit log", icon: <ScrollText />, count: d.audit_logs.length },
            ]}
          >
            <TabPanel value="blocks" className="mt-4">
              <Table columns={blockCols} rows={d.blocks} rowKey={(b) => b.block_index} pageSize={8} caption="Recent blocks" onRowClick={(b) => navigate(`/app/auditor/blocks/${b.block_index}`)} />
              <p className="mt-2 text-xs text-muted-foreground">Select a block to inspect its Merkle root, signatures and transactions.</p>
            </TabPanel>
            <TabPanel value="txs" className="mt-4">
              <p className="mb-3 text-xs text-muted-foreground">No voter identity is stored on-chain. Payloads are encrypted.</p>
              <Table columns={txCols} rows={d.transactions} rowKey={(t) => t.tx_hash} pageSize={8} caption="Recent transactions" empty={<EmptyState icon={<ListTree />} title="No transactions yet" description="Transactions appear once voters cast ballots." />} />
            </TabPanel>
            <TabPanel value="log" className="mt-4">
              <AuditTable logs={d.audit_logs} pageSize={8} empty={<EmptyState icon={<ScrollText />} title="No audit events yet" />} />
            </TabPanel>
          </Tabs>
        </StaggerItem>
      </Stagger>
    </>
  );
}

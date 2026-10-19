import { ArrowLeft, ArrowLeftRight, Blocks, KeyRound } from "lucide-react";
import { Link, useParams } from "react-router";

import { Hash, HashBlock } from "@/components/domain/common";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table, type Column } from "@/components/ui/Table";
import { useBlock } from "@/lib/queries";
import type { Transaction } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import axios from "axios";

export default function BlockDetail() {
  const index = Number(useParams().index);
  const q = useBlock(index);
  useBreadcrumb(Number.isFinite(index) ? `Block ${index}` : null);

  const back = <Button asChild variant="secondary" magnetic={false}><Link to="/app/auditor"><ArrowLeft /> Back to audit</Link></Button>;

  if (q.isPending) return <><PageHeader title={`Block ${index}`} /><div className="space-y-4" role="status" aria-label="Loading block"><Skeleton className="h-72 rounded-2xl" /><Skeleton className="h-40 rounded-2xl" /></div></>;
  if (q.isError) {
    const missing = axios.isAxiosError(q.error) && q.error.response?.status === 404;
    return (
      <>
        <PageHeader title={`Block ${index}`} actions={back} />
        {missing ? (
          <EmptyState icon={<Blocks />} title="Block not found" description="The chain does not have a block with that number. Pick one from the audit page." action={back} />
        ) : (
          <ErrorState error={q.error} title="Could not load this block" onRetry={() => q.refetch()} />
        )}
      </>
    );
  }

  const { block, signatures, transactions, height } = q.data;
  const sigEntries = Object.entries(signatures);
  const txCols: Column<Transaction>[] = [
    { key: "tx", header: "Tx hash", cell: (t) => <Hash value={t.tx_hash} /> },
    { key: "ballot", header: "Ballot ID", cell: (t) => <Hash value={t.ballot_id} head={10} tail={4} /> },
    { key: "payload", header: "Encrypted payload", cell: (t) => <Hash value={t.encrypted_payload} head={14} tail={0} /> },
    { key: "nonce", header: "Nonce", cell: (t) => <Hash value={t.nonce} head={10} tail={0} /> },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Auditor"
        title={`Block ${block.block_index}`}
        description={<span className="inline-flex flex-wrap items-center gap-2">{block.block_index === 0 ? <Badge tone="violet">Genesis block</Badge> : null}{formatDate(block.timestamp, true)}</span>}
        actions={
          <>
            {block.block_index > 0 && <Button asChild variant="ghost" magnetic={false}><Link to={`/app/auditor/blocks/${block.block_index - 1}`}><ArrowLeftRight className="rotate-0" /> Previous block</Link></Button>}
            {block.block_index < height - 1 && <Button asChild variant="ghost" magnetic={false}><Link to={`/app/auditor/blocks/${block.block_index + 1}`}>Next block</Link></Button>}
            {back}
          </>
        }
      />
      <div className="space-y-4">
        <Card>
          <CardHeader title="Block header" icon={<Blocks />} />
          <CardBody className="space-y-4">
            <KeyValueList
              items={[
                { label: "Index", value: block.block_index },
                { label: "Timestamp", value: formatDate(block.timestamp, true) },
                { label: "Transactions", value: block.transaction_count },
              ]}
            />
            <div className="space-y-3">
              <div><div className="mb-1 text-xs text-muted-foreground">Previous hash</div><HashBlock value={block.previous_hash} /></div>
              <div><div className="mb-1 text-xs text-muted-foreground">Merkle root</div><HashBlock value={block.merkle_root} /></div>
              <div><div className="mb-1 text-xs text-muted-foreground">Block hash</div><HashBlock value={block.block_hash} /></div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Validator signatures" description={`${sigEntries.length} of 3 validators signed (quorum 2)`} icon={<KeyRound />} />
          <CardBody className="space-y-3">
            {sigEntries.length === 0 ? <p className="text-sm text-muted-foreground">No signatures are recorded for this block.</p> : sigEntries.map(([node, sig]) => (
              <div key={node}>
                <div className="mb-1 flex items-center gap-2 text-sm font-medium">{node} <Badge tone="success">Signed</Badge></div>
                <HashBlock value={sig} />
              </div>
            ))}
          </CardBody>
        </Card>

        <div>
          <h2 className="mb-3 font-display text-xl font-semibold">Transactions</h2>
          <Table
            columns={txCols}
            rows={transactions}
            rowKey={(t) => t.tx_hash}
            caption="Transactions in this block"
            empty={<EmptyState icon={<Blocks />} title="No transactions in this block" description={block.block_index === 0 ? "The genesis block carries no transactions." : "This block is empty."} />}
          />
        </div>
      </div>
    </>
  );
}

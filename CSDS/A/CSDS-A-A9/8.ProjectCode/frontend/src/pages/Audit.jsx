import { ScrollText, ShieldCheck, ShieldX } from 'lucide-react'
import { Badge, Button, Card, EmptyState, PageHeader, useToast } from '../components/ui'
import { api } from '../lib/api'
import Gate from './Gate'
import { AuditTable } from './shared'
import { useAction } from './useAction'

function AuditView({ s }) {
  const { busy, run } = useAction()
  const toast = useToast()
  const verify = async () => {
    const r = await run('verify', api.verifyAudit)
    if (r) toast({ kind: r.valid ? 'success' : 'error', title: r.valid ? 'Hash chain verified' : 'Hash chain broken', message: r.detail, duration: r.valid ? 5000 : 9000 })
  }
  const { audit } = s
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Step 4"
        icon={ScrollText}
        title="Compliance audit"
        lead="Training and deletion events are chained with SHA-256, so any later edit to the ledger is detectable."
        actions={
          <Button icon={audit.valid ? ShieldCheck : ShieldX} loading={busy === 'verify'} disabled={busy != null} onClick={verify}>
            Verify hash chain
          </Button>
        }
      />
      <Card
        hover={false}
        title="Chain status"
        actions={
          <Badge tone={audit.valid ? 'mint' : 'rose'} dot>
            {audit.valid ? 'Valid' : 'Broken'}
          </Badge>
        }
      >
        <p role="status">{audit.detail}</p>
        <p className="muted small" style={{ marginTop: 6 }}>
          {audit.records.length} record(s) · the ledger survives new sessions and server restarts.
        </p>
      </Card>
      <Card hover={false} title="Ledger" subtitle="Select View on a row for the full record">
        {audit.records.length === 0 ? (
          <EmptyState
            icon={ScrollText}
            title="No audit events yet"
            message="Training and unlearning requests are recorded here as they happen."
            action={<Button to="/app/training">Train the model</Button>}
            compact
          />
        ) : (
          <AuditTable records={audit.records} />
        )}
      </Card>
    </div>
  )
}

export default function Audit() {
  return <Gate kpis={0} blocks={1}>{(s) => <AuditView s={s} />}</Gate>
}

import { useState } from 'react'
import { Download, Eye, ShieldAlert, ShieldCheck } from 'lucide-react'
import { Badge, Button, KeyValueList, Modal, Table } from '../components/ui'
import { fmtNum, fmtPct } from '../lib/format'
import { api } from '../lib/api'
import { sci, short, utc } from '../lib/fmt'

export const clientBadge = (c, trained) =>
  !trained ? (
    <Badge tone="neutral">Not trained</Badge>
  ) : c.active ? (
    <Badge tone="mint" dot>
      Active
    </Badge>
  ) : (
    <Badge tone="rose" dot>
      Removed
    </Badge>
  )

export const statusBadge = (status) =>
  status === 'CERTIFIED' ? (
    <Badge tone="mint" icon={ShieldCheck}>
      Certified
    </Badge>
  ) : status === 'REVIEW_REQUIRED' ? (
    <Badge tone="peach" icon={ShieldAlert}>
      Review required
    </Badge>
  ) : (
    <Badge tone="neutral">{status || '–'}</Badge>
  )

export function ClientsTable({ contributions, trained }) {
  const columns = [
    { key: 'display_name', label: 'Client', render: (c) => <strong>{c.display_name}</strong>, sortValue: (c) => c.display_name },
    { key: 'domain', label: 'Domain' },
    { key: 'record_count', label: 'Records', numeric: true },
    { key: 'original_norm', label: 'Original L2', numeric: true, render: (c) => (trained ? fmtNum(c.original_norm, 3) : '–') },
    { key: 'clipped_norm', label: 'Clipped L2', numeric: true, render: (c) => (trained ? fmtNum(c.clipped_norm, 3) : '–') },
    { key: 'clip_scale', label: 'Clip scale', numeric: true, render: (c) => (trained ? fmtNum(c.clip_scale, 3) : '–') },
    { key: 'active', label: 'State', render: (c) => clientBadge(c, trained), sortValue: (c) => (c.active ? 1 : 0) },
  ]
  return (
    <Table
      columns={columns}
      rows={contributions}
      rowKey={(c) => c.client_id}
      pageSize={0}
      caption="Federated clients and their tracked updates"
      cardTitle={(c) => `${c.display_name} · ${c.domain}`}
    />
  )
}

const hashStyle = { wordBreak: 'break-all' }

export function CertificateView({ cert }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const download = async () => {
    setBusy(true)
    setErr(null)
    try {
      const data = await api.latestCertificate()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${data.certificate_id}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stack">
      <div className="row between" style={{ flexWrap: 'wrap' }}>
        <div>
          <div className="row" style={{ '--gap': '10px', flexWrap: 'wrap' }}>
            {statusBadge(cert.status)}
            <span className="mono small">{cert.certificate_id}</span>
          </div>
          <p className="muted small" style={{ marginTop: 6 }}>
            {cert.client_name} · {utc(cert.issued_at_utc)}
          </p>
        </div>
        <Button variant="secondary" icon={Download} loading={busy} onClick={download}>
          Download JSON
        </Button>
      </div>
      {err && (
        <p className="field-error" role="alert">
          Download failed: {err}. Check that the API is running, then retry.
        </p>
      )}
      <KeyValueList
        items={[
          ['Privacy guarantee', `ε ${fmtNum(cert.epsilon, 4)} · δ ${cert.delta}`],
          ['Utility retained', `${fmtNum(cert.utility_retention_percent, 2)}%`],
          ['Residual influence (L2)', sci(cert.residual_influence_l2)],
          ['Reference retrain (L2)', sci(cert.reference_retrain_l2)],
          ['Membership AUC', `${fmtNum(cert.membership_auc_before, 3)} → ${fmtNum(cert.membership_auc_after, 3)}`],
          ['Perplexity', `${fmtNum(cert.perplexity_before, 3)} → ${fmtNum(cert.perplexity_after, 3)}`],
          ['Next-char accuracy', `${fmtPct(cert.accuracy_before)} → ${fmtPct(cert.accuracy_after)}`],
          ['Clients', `${cert.clients_before} → ${cert.clients_after}`],
          ['Clip norm · noise', `${cert.clip_norm} · ${cert.noise_multiplier}`],
          ['Method', cert.method],
          [
            'Model hash before',
            <span className="mono small" key="b" style={hashStyle}>
              {cert.model_hash_before}
            </span>,
          ],
          [
            'Model hash after',
            <span className="mono small" key="a" style={hashStyle}>
              {cert.model_hash_after}
            </span>,
          ],
          [
            'Audit record hash',
            <span className="mono small" key="h" style={hashStyle}>
              {cert.audit_record_hash}
            </span>,
          ],
        ]}
      />
    </div>
  )
}

export function AuditTable({ records, pageSize = 8 }) {
  const [open, setOpen] = useState(null)
  const isUnlearn = (r) => r.event_type === 'CLIENT_UNLEARNING'
  const columns = [
    { key: 'sequence', label: '#', numeric: true },
    {
      key: 'event_type',
      label: 'Event',
      render: (r) => <Badge tone={isUnlearn(r) ? 'peach' : 'sky'}>{isUnlearn(r) ? 'Unlearning' : 'Training'}</Badge>,
      sortValue: (r) => r.event_type,
    },
    { key: 'time', label: 'Time (UTC)', render: (r) => utc(r.timestamp_utc || r.issued_at_utc), sortValue: (r) => r.timestamp_utc || r.issued_at_utc || '' },
    { key: 'client_id', label: 'Client', render: (r) => r.client_name || r.client_id || '–' },
    { key: 'status', label: 'Status', render: (r) => (r.status ? statusBadge(r.status) : '–') },
    {
      key: 'record_hash',
      label: 'Record hash',
      sortable: false,
      render: (r) => (
        <span className="mono small" title={r.record_hash}>
          {short(r.record_hash, 18)}
        </span>
      ),
    },
    {
      key: 'view',
      label: '',
      sortable: false,
      render: (r) => (
        <Button variant="ghost" size="sm" icon={Eye} onClick={() => setOpen(r)} aria-label={`View record ${r.sequence}`}>
          View
        </Button>
      ),
    },
  ]
  return (
    <>
      <Table
        columns={columns}
        rows={records}
        rowKey={(r) => r.sequence}
        pageSize={pageSize}
        initialSort={{ key: 'sequence', dir: 'desc' }}
        searchKeys={['event_type', 'client_id', 'client_name', 'status', 'record_hash']}
        searchPlaceholder="Search the ledger"
        caption="Hash-chained compliance audit ledger"
        cardTitle={(r) => `#${r.sequence} · ${isUnlearn(r) ? 'Unlearning' : 'Training'}`}
      />
      <Modal open={!!open} onClose={() => setOpen(null)} title={open ? `Audit record #${open.sequence}` : 'Audit record'} description="Full ledger entry, including the link to the previous record.">
        {open && (
          <pre className="mono small" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '55vh', overflow: 'auto', background: 'var(--surface-2)', padding: 14, borderRadius: 14 }}>
            {JSON.stringify(open, null, 2)}
          </pre>
        )}
      </Modal>
    </>
  )
}

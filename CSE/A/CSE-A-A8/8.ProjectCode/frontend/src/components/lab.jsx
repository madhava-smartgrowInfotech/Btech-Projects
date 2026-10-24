import { useState } from 'react'
import { AlertTriangle, FlaskConical, ShieldAlert } from 'lucide-react'
import { Badge, Button, Card, Skeleton, Table, useToast } from './ui'
import { api } from '../lib/api'
import { REPORT_STATUS, STATUS, value } from '../lib/format'
import { useConfig } from '../lib/config'

export function StatusBadge({ status }) {
  const s = STATUS[status] || STATUS.UNKNOWN
  return (
    <Badge tone={s.tone} dot>
      {s.label}
    </Badge>
  )
}

export function ReportStatusBadge({ status }) {
  const s = REPORT_STATUS[status] || { label: status || 'Unknown', tone: 'neutral' }
  return (
    <Badge tone={s.tone} dot>
      {s.label}
    </Badge>
  )
}

export function Callout({ tone = 'info', icon: Icon = ShieldAlert, title, children }) {
  return (
    <div className={`callout callout-${tone}`} role={tone === 'danger' ? 'alert' : 'note'}>
      <Icon size={18} aria-hidden="true" style={{ flexShrink: 0, marginTop: 2 }} />
      <div>
        {title && <strong>{title} </strong>}
        {children}
      </div>
    </div>
  )
}

export function Disclaimer() {
  const { config } = useConfig()
  return (
    <Callout title="Medical disclaimer:">{config ? config.disclaimer : <Skeleton width="70%" height={14} style={{ display: 'inline-block' }} />}</Callout>
  )
}

export function CriticalBanner({ count }) {
  if (!count) return null
  return (
    <Callout tone="danger" icon={AlertTriangle} title={`${count} result${count === 1 ? ' is' : 's are'} far outside the reference range.`}>
      Please review {count === 1 ? 'it' : 'them'} in Report analysis and consider consulting a doctor.
    </Callout>
  )
}

export function resultColumns() {
  return [
    { key: 'test_name', label: 'Test', render: (r) => <strong>{r.test_name}</strong> },
    {
      key: 'result_value',
      label: 'Result',
      num: true,
      render: (r) => (
        <span className="val">
          {value(r.result_value)} <span className="faint">{r.unit}</span>
        </span>
      ),
    },
    { key: 'reference_range', label: 'Reference range', num: true, sortable: false, render: (r) => <span className="faint">{r.reference_range}</span> },
    { key: 'status', label: 'Status', render: (r) => <StatusBadge status={r.status} />, sortValue: (r) => ({ HIGH: 3, LOW: 2, UNKNOWN: 1, NORMAL: 0 })[r.status] ?? 0 },
  ]
}

export function ResultsTable({ results, pageSize = 20, empty, caption = 'Lab test results' }) {
  return <Table columns={resultColumns()} rows={results} rowKey={(r) => r.id} pageSize={pageSize} empty={empty} caption={caption} />
}

export function InsightCard({ result }) {
  const ins = result.insight
  return (
    <Card className="insight-card" pad>
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ minWidth: 0 }}>
          <h3 className="break">{result.test_name}</h3>
          <div className="faint val">
            {value(result.result_value)} {result.unit} · reference {result.reference_range}
          </div>
          {result.file_name && <div className="faint" style={{ fontSize: 12.5 }}>From {result.file_name}</div>}
        </div>
        <StatusBadge status={result.status} />
      </div>
      {ins ? (
        <>
          <section className="insight-section">
            <h4>What this measures</h4>
            <p>{ins.explanation}</p>
          </section>
          <section className="insight-section">
            <h4>Possible general causes</h4>
            <p>{ins.possible_causes}</p>
          </section>
          <section className="insight-section">
            <h4>Suggestion</h4>
            <p>{ins.recommendations}</p>
          </section>
        </>
      ) : (
        <p className="muted" style={{ marginTop: 12 }}>
          No insight was generated for this result.
        </p>
      )}
    </Card>
  )
}

export function PageSkeleton({ cards = 4 }) {
  return (
    <div className="container" aria-busy="true" aria-label="Loading page">
      <Skeleton width={180} height={14} />
      <Skeleton width="45%" height={34} style={{ margin: '14px 0 28px' }} />
      <div className="grid grid-4">
        {Array.from({ length: cards }).map((_, i) => (
          <Skeleton key={i} height={128} radius={12} />
        ))}
      </div>
      <Skeleton height={320} radius={12} style={{ marginTop: 18 }} />
    </div>
  )
}

// Loads the five synthetic sample reports (through the real pipeline) into an empty library.
export function SampleDataButton({ onDone, variant = 'secondary' }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const run = async () => {
    setBusy(true)
    try {
      const res = await api.seedDemo()
      toast({ title: 'Sample reports loaded', message: `${res.created.length} synthetic reports were processed by the pipeline.` })
      onDone?.()
    } catch (err) {
      toast({ title: 'Could not load sample reports', message: err.message, tone: 'error' })
    } finally {
      setBusy(false)
    }
  }
  return (
    <Button variant={variant} icon={FlaskConical} loading={busy} onClick={run}>
      Load sample reports
    </Button>
  )
}

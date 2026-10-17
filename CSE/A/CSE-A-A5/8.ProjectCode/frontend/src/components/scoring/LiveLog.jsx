import { Eraser, Radio } from 'lucide-react'
import { clock, pct } from '../../format'
import { clearScored, useScored } from '../../lib/session'
import { Button } from '../ui/controls'
import { Badge, Card, Severity } from '../ui/display'
import { EmptyState } from '../ui/feedback'
import Table from '../ui/Table'

export default function LiveLog() {
  const log = useScored()
  const attacks = log.filter((e) => e.label === 'attack').length

  const columns = [
    { key: 'time', label: 'Time', sortable: true, render: (r) => <span className="font-mono text-xs text-muted">{clock(r.time)}</span> },
    { key: 'label', label: 'Verdict', sortable: true, render: (r) => <Badge tone={r.label === 'attack' ? 'alert' : 'ok'} dot>{r.label}</Badge> },
    { key: 'confidence', label: 'Confidence', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.confidence) },
    { key: 'flow', label: 'Proto / service / state', render: (r) => <span className="font-mono text-xs text-muted">{r.proto}/{r.service}/{r.state}</span> },
    { key: 'scores', label: 'XGB / CNN', render: (r) => <span className="font-mono text-xs tabular-nums text-muted">{pct(r.xgb)} / {pct(r.cnn)}</span> },
    { key: 'severity', label: 'Severity', render: (r) => <Severity s={r.severity} /> },
  ]

  return (
    <Card title="Live classification log" eyebrow={`${log.length} scored this session`}
      action={<Button variant="ghost" size="sm" icon={Eraser} onClick={clearScored} disabled={!log.length}>Clear</Button>}>
      <div className="mb-3 font-mono text-xs text-muted" aria-live="polite">
        Total <span className="text-fg">{log.length}</span> - attacks <span className="text-alert">{attacks}</span> - normal <span className="text-ok">{log.length - attacks}</span>
      </div>
      <Table columns={columns} rows={log} rowKey={(r) => r.id} pageSize={10} caption="Records scored in this session"
        empty={<EmptyState icon={Radio} title="Nothing scored yet" body="Records you score here (and the first 50 rows of any batch) appear in this log."
          action={<Button variant="secondary" size="sm" onClick={() => document.getElementById('score')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>Score a record</Button>} />}
        cards={(r) => (
          <div className="flex items-center justify-between gap-2 rounded border border-line bg-panel-2 p-3 text-xs">
            <span className="font-mono text-muted">{clock(r.time)} {r.proto}/{r.service}</span>
            <Badge tone={r.label === 'attack' ? 'alert' : 'ok'} dot>{r.label}</Badge>
            <span className="font-mono tabular-nums">{pct(r.confidence)}</span>
          </div>
        )} />
    </Card>
  )
}

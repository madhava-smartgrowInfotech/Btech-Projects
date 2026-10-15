import { useEffect, useState } from 'react'
import { ScrollText } from 'lucide-react'
import api, { describeError } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Badge, Card } from '../components/ui/display'
import { Select } from '../components/ui/controls'
import { EmptyState, ErrorState } from '../components/ui/feedback'
import Table from '../components/ui/Table'

const OPS = [
  ['', 'All operations'], ['send', 'send'], ['receive', 'receive'], ['key_generate', 'key_generate'], ['key_import', 'key_import'],
  ['key_export_private', 'key_export_private'], ['key_delete', 'key_delete'], ['robustness', 'robustness'], ['benchmark', 'benchmark'],
  ['login', 'login'], ['register', 'register'],
]

function summary(e) {
  const d = e.details
  if (!e.ok) return d.error || 'failed'
  if (e.op === 'send') return `${d.filename} (${d.payload_bytes} B) into ${d.cover} · PSNR ${d.quality?.psnr_db} dB · SSIM ${d.quality?.ssim}`
  if (e.op === 'receive') return `${d.filename} (${d.output_bytes} B) · hash ${d.hash_match ? 'match' : 'MISMATCH'}`
  if (e.op.startsWith('key')) return `${d.bits ? `${d.bits}-bit ` : ''}${d.fingerprint || ''}`
  if (e.op === 'robustness') return `survived ${d.survived?.length ?? 0} · lost ${d.lost?.length ?? 0}`
  if (e.op === 'benchmark') return `${d.covers} covers · ${d.rows} runs`
  return ''
}

export default function Log() {
  const [rows, setRows] = useState(null)
  const [filter, setFilter] = useState('')
  const [open, setOpen] = useState(null)
  const [error, setError] = useState(null)

  const load = (op) => {
    setRows(null)
    setError(null)
    return api.get('/log', { params: { op: op || undefined, limit: 200 } })
      .then((r) => setRows(r.data))
      .catch((e) => setError(describeError(e)))
  }
  useEffect(() => { load(filter) }, [filter])

  const selected = rows?.find((r) => r.id === open)

  const columns = [
    { key: 'id', label: '#', render: (e) => (
      <button type="button" aria-expanded={open === e.id} onClick={() => setOpen(open === e.id ? null : e.id)}
        className="font-mono text-xs text-dim hover:text-ok">#{e.id}</button>
    ) },
    { key: 'when', label: 'When', className: 'whitespace-nowrap text-muted', render: (e) => new Date(e.created_at).toLocaleString() },
    { key: 'op', label: 'Operation', render: (e) => <span className="font-mono text-xs text-fg">{e.op}</span> },
    { key: 'status', label: 'Status', render: (e) => <Badge tone={e.ok ? 'ok' : 'alert'} dot>{e.ok ? 'ok' : 'failed'}</Badge> },
    { key: 'details', label: 'Details', className: 'text-muted', render: (e) => summary(e) },
  ]

  return (
    <>
      <PageHeader title="Operation log"
        subtitle="Every operation with sizes, timings and metrics. Keys, passwords and file contents are never recorded." />

      <div className="mb-4 max-w-xs">
        <Select label="Filter" value={filter} onChange={(e) => setFilter(e.target.value)} options={OPS} />
      </div>

      <Card title="Operations" bodyClass="px-4 pb-2 pt-0">
        {error && <div className="mb-3"><ErrorState error={error} onRetry={() => load(filter)} /></div>}
        <Table
          caption="Logged operations, newest first"
          columns={columns}
          rows={error ? null : rows}
          rowKey={(e) => e.id}
          loading={rows === null && !error}
          pageSize={20}
          footer={rows ? `${rows.length} shown${rows.length >= 200 ? ' (latest 200)' : ''}` : undefined}
          empty={!error && (
            <EmptyState icon={ScrollText} title={filter ? `No "${filter}" operations yet` : 'Nothing logged yet'}
              body="Operations appear here as you use the app: keys, sends, receives, attacks and benchmarks." />
          )}
        />
      </Card>

      {selected && (
        <div className="mt-4">
          <Card title={`Operation #${selected.id}`} eyebrow={selected.op} action={
            <button type="button" onClick={() => setOpen(null)} className="font-mono text-[11px] uppercase text-dim hover:text-fg">close</button>
          }>
            <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-muted">{JSON.stringify(selected.details, null, 2)}</pre>
          </Card>
        </div>
      )}
    </>
  )
}

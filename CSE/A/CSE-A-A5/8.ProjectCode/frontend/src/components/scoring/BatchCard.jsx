import { FileSpreadsheet, UploadCloud } from 'lucide-react'
import { useMemo, useState } from 'react'
import api, { describeError } from '../../api'
import { logEvent } from '../../lib/activity'
import { readFlowMeta } from '../../lib/csv'
import { pushScored } from '../../lib/session'
import { pct, severityOf, num } from '../../format'
import { Button, FileDrop } from '../ui/controls'
import { Badge, Card, KeyValueList, ScoreBar, Severity } from '../ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../ui/feedback'
import Table from '../ui/Table'

const MAX_BYTES = 10 * 1024 * 1024

export default function BatchCard() {
  const toast = useToast()
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [state, setState] = useState({ loading: false, error: null, data: null, meta: [], name: '' })

  function pick(files) {
    const f = files[0]
    setFileError(null)
    if (!f) { setFile(null); return }
    if (!f.name.toLowerCase().endsWith('.csv')) { setFile(null); setFileError('That is not a .csv file. Export your flow records as CSV and try again.'); return }
    if (f.size > MAX_BYTES) { setFile(null); setFileError('The file is over the 10 MB limit. Split it into smaller CSVs.'); return }
    setFile(f)
  }

  async function run(f) {
    setState({ loading: true, error: null, data: null, meta: [], name: f.name })
    try {
      const text = await f.text()
      const meta = readFlowMeta(text)
      const fd = new FormData()
      fd.append('file', f)
      const { data } = await api.post('/ids/score-batch', fd)
      setState({ loading: false, error: null, data, meta, name: f.name })
      // first 50 rows join the session log, like single scores do
      pushScored(data.results.slice(0, 50).map((r) => ({
        source: 'batch', label: r.label, confidence: r.confidence, severity: severityOf(r.label, r.confidence),
        proto: meta[r.row]?.proto ?? '-', service: meta[r.row]?.service ?? '-', state: meta[r.row]?.state ?? '-', xgb: r.xgb_score, cnn: r.cnn_score,
      })))
      logEvent('ids', `batch ${f.name}: ${data.total} rows, ${data.attack_count} attacks`)
      toast({ tone: data.attack_count ? 'warn' : 'ok', title: `Scored ${num(data.total)} rows`, body: `${num(data.attack_count)} attacks, ${num(data.normal_count)} normal.` })
    } catch (e) {
      setState({ loading: false, error: describeError(e), data: null, meta: [], name: f.name })
    }
  }

  async function sample() {
    try {
      const res = await fetch('/samples/sample_flows.csv')
      if (!res.ok) throw new Error(`sample file returned ${res.status}`)
      const blob = await res.blob()
      const f = new File([blob], 'sample_flows.csv', { type: 'text/csv' })
      setFile(f)
      setFileError(null)
      run(f)
    } catch (e) {
      setFileError(`Could not load the bundled sample: ${e.message}`)
    }
  }

  const { data, meta, loading, error } = state
  const rows = useMemo(() => (data ? data.results.map((r) => ({ ...r, ...meta[r.row] })) : null), [data, meta])
  const labelled = rows ? rows.filter((r) => r.truth) : []
  const agree = labelled.filter((r) => r.truth === r.label).length

  const columns = [
    { key: 'row', label: 'Row', sortable: true, render: (r) => <span className="font-mono text-muted">#{r.row + 1}</span> },
    { key: 'label', label: 'Verdict', sortable: true, render: (r) => <Badge tone={r.label === 'attack' ? 'alert' : 'ok'} dot>{r.label}</Badge> },
    { key: 'confidence', label: 'Confidence', sortable: true, align: 'right', className: 'font-mono tabular-nums', render: (r) => pct(r.confidence) },
    { key: 'flow', label: 'Proto / service / state', render: (r) => <span className="font-mono text-xs text-muted">{r.proto ?? '-'}/{r.service ?? '-'}/{r.state ?? '-'}</span> },
    { key: 'xgb_score', label: 'XGB', sortable: true, align: 'right', className: 'font-mono tabular-nums text-muted', render: (r) => pct(r.xgb_score) },
    { key: 'cnn_score', label: 'CNN', sortable: true, align: 'right', className: 'font-mono tabular-nums text-muted', render: (r) => pct(r.cnn_score) },
    { key: 'severity', label: 'Severity', render: (r) => <Severity s={severityOf(r.label, r.confidence)} /> },
  ]

  return (
    <Card title="Batch CSV scoring" eyebrow="POST /api/ids/score-batch">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-3">
          <p className="text-xs text-muted">UNSW-NB15 style CSV, up to 10 MB and 10,000 rows. Missing feature columns are filled with defaults by the API.</p>
          <FileDrop label="Drop a flow CSV here" accept=".csv,text/csv" multiple={false} onFiles={pick} />
          {fileError && <ErrorState compact error={fileError} title="Cannot use that file" />}
          <div className="flex flex-wrap gap-2">
            <Button icon={UploadCloud} loading={loading} disabled={!file} onClick={() => run(file)}>Upload and score</Button>
            <Button variant="secondary" icon={FileSpreadsheet} disabled={loading} onClick={sample}>Use sample (120 flows)</Button>
          </div>
          <p className="text-[11px] text-dim">The sample is 120 random rows from data/raw/synthetic_demo.csv, the dataset the model was trained on.</p>
        </div>

        <div className="min-w-0 lg:col-span-2" aria-live="polite" aria-busy={loading}>
          {loading && <div className="space-y-2"><Skeleton className="h-6 w-56" /><Skeleton className="h-24 w-full" /><Skeleton className="h-40 w-full" /></div>}
          {!loading && error && <ErrorState error={error} title="Batch scoring failed" onRetry={file ? () => run(file) : undefined} />}
          {!loading && !error && !data && (
            <EmptyState icon={FileSpreadsheet} title="No batch scored yet" body="Choose a CSV, or use the bundled sample to see the engine score 120 real flows." />
          )}
          {!loading && !error && data && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <KeyValueList items={[
                  ['File', state.name], ['Rows scored', num(data.total)],
                  ['Attacks', <span key="a" className="text-alert">{num(data.attack_count)}</span>],
                  ['Normal', <span key="n" className="text-ok">{num(data.normal_count)}</span>],
                  ...(labelled.length ? [['Agrees with CSV label', `${agree} / ${labelled.length} (${pct(agree / labelled.length)})`]] : []),
                ]} />
                <div className="space-y-3 self-center">
                  <ScoreBar value={data.total ? data.attack_count / data.total : 0} label="Share flagged as attack" />
                  {data.total > data.results.length && <p className="text-[11px] text-dim">The API returns the first {num(data.results.length)} rows; counts cover all {num(data.total)}.</p>}
                </div>
              </div>
              <Table columns={columns} rows={rows} rowKey={(r) => r.row} pageSize={8} initialSort={{ key: 'row', dir: 'asc' }} caption="Per-row batch results"
                footer={`${num(rows.length)} rows shown`}
                cards={(r) => (
                  <div className="flex items-center justify-between gap-2 rounded border border-line bg-panel-2 p-3 text-xs">
                    <span className="font-mono text-muted">#{r.row + 1} {r.proto ?? '-'}/{r.service ?? '-'}</span>
                    <Badge tone={r.label === 'attack' ? 'alert' : 'ok'} dot>{r.label}</Badge>
                    <span className="font-mono tabular-nums">{pct(r.confidence)}</span>
                  </div>
                )} />
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}

import { useState } from 'react'
import { AlertTriangle, Download, FileSpreadsheet, FileText, ShieldAlert, ShieldCheck, Sigma } from 'lucide-react'
import { api } from '../lib/api'
import { fmtInt, fmtPct, fmtUSD } from '../lib/format'
import { RISK_TONE } from '../lib/labels'
import { Badge, Button, Card, EmptyState, ErrorState, FileDrop, PageHeader, ProgressBar, Skeleton, StatCard, Stepper, Table, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import ConfusionMatrix from '../components/app/ConfusionMatrix'
import MetricTiles from '../components/app/MetricTiles'

const REQUIRED = ['Amount', 'Time', 'Merchant_Category', 'Transaction_Type', 'Card_Present', 'Country_Match', ...Array.from({ length: 22 }, (_, i) => `V${i + 1}`)]

/** Header columns the file is missing (the API fills these with 0 rather than rejecting the file). */
async function missingColumns(file) {
  const first = (await file.slice(0, 8192).text()).split(/\r?\n/)[0]
  const have = first.split(',').map((c) => c.trim().replace(/^"|"$/g, ''))
  return REQUIRED.filter((c) => !have.includes(c))
}

const STEPS = [{ label: 'Choose file' }, { label: 'Analyse' }, { label: 'Review' }]

const COLUMNS = [
  { key: 'row', label: '#', numeric: true, sortValue: (r) => r.row },
  { key: 'Amount', label: 'Amount', numeric: true, render: (r) => fmtUSD(r.Amount), sortValue: (r) => r.Amount },
  { key: 'Merchant_Category', label: 'Merchant' },
  { key: 'Transaction_Type', label: 'Channel' },
  {
    key: 'Fraud_Probability',
    label: 'Fraud probability',
    sortValue: (r) => r.Fraud_Probability,
    render: (r) => (
      <span className="prob-cell">
        <ProgressBar value={r.Fraud_Probability} tone={RISK_TONE[r.Risk] || 'mint'} label="Fraud probability" height={8} />
        <span className="num">{fmtPct(r.Fraud_Probability)}</span>
      </span>
    ),
  },
  { key: 'Risk', label: 'Risk', render: (r) => <Badge tone={RISK_TONE[r.Risk] || 'neutral'} dot>{r.Risk}</Badge> },
  {
    key: 'Predicted_Class',
    label: 'Verdict',
    render: (r) => (r.Predicted_Class === 1 ? <Badge tone="rose" icon={ShieldAlert}>Flagged</Badge> : <Badge tone="mint" icon={ShieldCheck}>Approved</Badge>),
  },
]

export default function Bulk() {
  const toast = useToast()
  const [file, setFile] = useState(null)
  const [state, setState] = useState({ status: 'idle', res: null, error: null, name: '', missing: [] })

  const analyse = async (f) => {
    if (!f) return
    setState({ status: 'loading', res: null, error: null, name: f.name, missing: [] })
    try {
      const missing = await missingColumns(f)
      const res = await api.predictBatch(f)
      setState({ status: 'done', res, error: null, name: f.name, missing })
      toast({ kind: 'success', title: 'Analysis complete', message: `${fmtInt(res.rows)} transactions screened, ${fmtInt(res.fraud_detected)} flagged.` })
    } catch (error) {
      setState({ status: 'error', res: null, error, name: f.name, missing: [] })
    }
  }

  const trySample = async () => {
    try {
      const r = await fetch(api.sampleUrl)
      if (!r.ok) throw new Error('The sample file is not available.')
      const blob = await r.blob()
      const f = new File([blob], 'sample_batch.csv', { type: 'text/csv' })
      setFile(null)
      analyse(f)
    } catch (e) {
      setState({ status: 'error', res: null, error: e, name: 'sample_batch.csv', missing: [] })
    }
  }

  const step = state.status === 'done' ? 3 : state.status === 'loading' ? 1 : file ? 1 : 0
  const res = state.res
  const rows = res ? res.preview.map((r, i) => ({ ...r, row: i + 1 })) : []
  const allFlagged = res && res.rows >= 5 && res.fraud_detected === res.rows

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Batch screening"
        icon={FileSpreadsheet}
        title="Bulk verification"
        lead="Upload a CSV of transactions and screen the whole file at once. Add a Class column to see accuracy against known labels."
      />
      <Stepper steps={STEPS} current={step} label="Bulk verification steps" />
      <div className="grid-2 wide-left" style={{ alignItems: 'start' }}>
        <Card title="Your file" hover={false} className="sticky-side">
          <div className="stack">
            <FileDrop accept=".csv,text/csv" label="Drop a CSV here or click to browse" hint="Needs Amount, Time, Merchant_Category, Transaction_Type, Card_Present, Country_Match and V1 to V22" onFiles={(fs) => setFile(fs[0] || null)} />
            <Button icon={FileSpreadsheet} block loading={state.status === 'loading'} disabled={!file} onClick={() => analyse(file)}>
              Upload and analyse
            </Button>
            <div className="row" style={{ '--gap': '8px' }}>
              <Button variant="secondary" size="sm" icon={FileText} onClick={trySample} disabled={state.status === 'loading'}>Try the sample file</Button>
              <Button variant="ghost" size="sm" icon={Download} onClick={() => { window.location.href = api.sampleUrl }}>Download sample</Button>
            </div>
            <p className="small muted">The sample has 20 labelled rows from the dataset, so metrics appear too.</p>
          </div>
        </Card>

        <div className="stack">
          {state.status === 'idle' && (
            <EmptyState
              icon={FileSpreadsheet}
              title="No file analysed yet"
              message="Choose a CSV on the left, or try the bundled sample to see how results look."
              action={<Button variant="secondary" onClick={trySample}>Try the sample file</Button>}
            />
          )}
          {state.status === 'loading' && (
            <Card title={`Analysing ${state.name}`} hover={false}>
              <div className="stack" role="status" aria-label="Analysing file">
                <ProgressBar indeterminate label="Analysing" />
                <Skeleton height={90} radius={18} />
                <Skeleton height={220} radius={18} />
              </div>
            </Card>
          )}
          {state.status === 'error' && <ErrorState title="The file could not be analysed" error={state.error} hint="Check that it is a CSV with the columns listed on the left, then try again." onRetry={() => (file ? analyse(file) : trySample())} />}
          {state.status === 'done' && (
            <SlideUp className="stack">
              <div className="grid-kpi">
                <StatCard label="Transactions" value={res.rows} format={fmtInt} icon={Sigma} tone="lavender" foot={state.name} />
                <StatCard label="Flagged as fraud" value={res.fraud_detected} format={fmtInt} icon={ShieldAlert} tone="rose" foot={fmtPct(res.fraud_detected / res.rows) + ' of the file'} />
                <StatCard label="Approved" value={res.rows - res.fraud_detected} format={fmtInt} icon={ShieldCheck} tone="mint" />
              </div>
              {state.missing.length > 0 && (
                <div className="notice warn" role="status">
                  <AlertTriangle size={18} aria-hidden="true" />
                  <span>
                    Your file has no {state.missing.length > 6 ? `${state.missing.slice(0, 6).join(', ')} and ${state.missing.length - 6} more` : state.missing.join(', ')} column{state.missing.length > 1 ? 's' : ''}. The API fills missing columns with 0, so treat these scores with care.
                  </span>
                </div>
              )}
              {allFlagged && (
                <div className="notice warn" role="status">
                  <AlertTriangle size={18} aria-hidden="true" />
                  <span>Every row was flagged. If that surprises you, check that the file's values are on the same scale as the training data.</span>
                </div>
              )}
              {res.metrics && (
                <Card title="Accuracy against your labels" subtitle="Your file includes a Class column, so predictions were scored." hover={false}>
                  <div className="stack">
                    <MetricTiles metrics={res.metrics} />
                    <ConfusionMatrix matrix={res.metrics.confusion_matrix} />
                  </div>
                </Card>
              )}
              <Card
                title="Predictions"
                subtitle={res.rows > res.preview.length ? `First ${res.preview.length} of ${fmtInt(res.rows)} rows. Download the CSV for all of them.` : `All ${res.rows} rows`}
                actions={<Button icon={Download} size="sm" onClick={() => { window.location.href = api.exportUrl }}>Download results (CSV)</Button>}
                hover={false}
              >
                <Table columns={COLUMNS} rows={rows} pageSize={0} caption="Batch predictions" rowKey={(r) => r.row} cardTitle={(r) => `Row ${r.row}`} />
              </Card>
            </SlideUp>
          )}
        </div>
      </div>
    </div>
  )
}

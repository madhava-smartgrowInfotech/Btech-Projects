import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, FileDown, Package, Play } from 'lucide-react'
import { PageHeader, Button, Card, FileDrop, StatCard, Switch, Table, useToast } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Callout, Gate, RiskBadge } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { downloadCsv, saveBlob } from '../lib/csv'
import { useAppState } from '../lib/appstate'
import { fmtInt, fmtNum } from '../lib/format'
import { RISK_HEX, RISK_ORDER, shortBand } from '../lib/risk'

export default function Batch() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Customers"
        icon={Package}
        title="Batch prediction"
        lead="Score a whole file of new customers at once. The file needs the same feature columns the active model was trained on."
      />
      <Gate need="model">
        <Body />
      </Gate>
    </div>
  )
}

function Body() {
  const toast = useToast()
  const { state } = useAppState()
  const cols = state?.model?.feature_cols || []
  const [file, setFile] = useState(null)
  const [rowCount, setRowCount] = useState(null)
  const [drivers, setDrivers] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [res, setRes] = useState(null)

  const onFiles = async (files) => {
    const f = files[0] || null
    setFile(f)
    setRes(null)
    setError('')
    if (!f) return setRowCount(null)
    try {
      const n = Math.max(0, (await f.text()).split(/\r?\n/).filter((l) => l.trim()).length - 1)
      setRowCount(n)
      setDrivers(n <= 300)
    } catch {
      setRowCount(null)
    }
  }

  const run = async () => {
    setBusy(true)
    setError('')
    try {
      const r = await api.batch(file, drivers)
      setRes(r)
      toast({ kind: 'success', title: `Scored ${fmtInt(r.total)} customers`, message: `${fmtInt(r.predicted_churn)} predicted to churn.` })
    } catch (e) {
      setRes(null)
      setError(e.message)
      toast({ kind: 'error', title: 'Batch prediction failed', message: e.message })
    } finally {
      setBusy(false)
    }
  }

  const template = async () => {
    try {
      saveBlob(await api.batchTemplate(), 'sample_batch.csv')
    } catch (e) {
      toast({ kind: 'error', title: 'Could not create the sample file', message: e.message })
    }
  }

  return (
    <>
      <Card title="1. Upload customers to score" subtitle="The active model expects these feature columns:">
        <div className="stack">
          <div className="chip-list">
            {cols.map((c) => (
              <span className="chip" key={c}>
                {c}
              </span>
            ))}
          </div>
          <div className="grid-2">
            <FileDrop accept=".csv,text/csv" label="Drop a CSV to score" hint="Extra columns such as the customer ID are kept in the results." onFiles={onFiles} />
            <div className="stack" style={{ justifyContent: 'center' }}>
              <p className="muted">No file to hand? Download 25 customers from the loaded dataset in exactly the right shape.</p>
              <div className="row">
                <Button variant="secondary" icon={FileDown} onClick={template}>
                  Download sample file
                </Button>
              </div>
              {file && rowCount != null && (
                <Callout tone="info">
                  {file.name}: {fmtInt(rowCount)} rows.
                </Callout>
              )}
            </div>
          </div>
          <Switch checked={drivers} onChange={setDrivers} label="Include top risk factors per customer" description="Slower for large files, so it switches off by default above 300 rows." />
          <div className="row">
            <Button icon={Play} onClick={run} loading={busy} disabled={!file}>
              Run batch prediction
            </Button>
            {!file && <span className="small muted">Choose a file first.</span>}
          </div>
          {error && (
            <Callout tone="error" title="This file could not be scored">
              {error}
              <div style={{ marginTop: 6 }}>Add the missing columns, or download the sample file to see the expected layout.</div>
            </Callout>
          )}
        </div>
      </Card>

      {res && (
        <>
          {res.missing_values > 0 && (
            <Callout tone="warn" title="Missing values were filled in">
              {fmtInt(res.missing_values)} missing values in the feature columns were imputed with the strategy learned during training.
            </Callout>
          )}
          <Stagger className="grid-kpi">
            <Stagger.Item><StatCard label="Customers scored" value={res.total} format={fmtInt} tone="lavender" foot={res.filename} /></Stagger.Item>
            <Stagger.Item><StatCard label="Predicted to churn" value={res.predicted_churn} format={fmtInt} tone="rose" foot="Probability of 50% or more" /></Stagger.Item>
            <Stagger.Item><StatCard label="Avg. churn probability" value={res.avg_probability} format={(v) => `${fmtNum(v, 1)}%`} tone="sky" /></Stagger.Item>
            <Stagger.Item><StatCard label="Critical risk" value={res.counts['Critical Risk'] || 0} format={fmtInt} tone="peach" /></Stagger.Item>
          </Stagger>
          <div className="stack">
            <Card
              title="Predictions"
              subtitle="Highest churn probability first"
              actions={
                <Button size="sm" variant="secondary" icon={Download} onClick={() => downloadCsv('churn_batch_predictions.csv', res.rows)}>
                  Download CSV
                </Button>
              }
            >
              <Table
                caption="Batch predictions"
                pageSize={10}
                searchKeys={['customerID']}
                searchPlaceholder="Search customer ID"
                rowKey={(r, i) => `${r.customerID}-${i}`}
                cardTitle={(r) => String(r.customerID)}
                columns={[
                  { key: 'customerID', label: 'Customer', render: (r) => String(r.customerID) },
                  { key: 'churn_probability', label: 'Churn probability', numeric: true, render: (r) => `${fmtNum(r.churn_probability, 1)}%` },
                  { key: 'predicted_churn', label: 'Predicted churn' },
                  { key: 'risk_category', label: 'Risk', render: (r) => <RiskBadge band={r.risk_category} short />, sortValue: (r) => RISK_ORDER.indexOf(r.risk_category) },
                  ...(res.drivers_included
                    ? [{ key: 'top_risk_factor_1', label: 'Top risk factors', wrap: true, sortable: false, render: (r) => [r.top_risk_factor_1, r.top_risk_factor_2, r.top_risk_factor_3].filter(Boolean).join(' · ') || '–' }]
                    : []),
                ]}
                rows={res.rows}
              />
            </Card>
            <Card title="Risk mix of this file">
              <BarCompare label="Batch customers per risk band" data={RISK_ORDER.map((b) => ({ name: shortBand(b), value: res.counts[b] || 0, color: RISK_HEX[b] }))} valueFormat={fmtInt} name="Customers" height={280} />
              <p className="section-note" style={{ marginTop: 10 }}>
                Want to look closer at someone? Open them in <Link className="link-cell" to="/app/customer">Customer 360</Link> if they exist in the loaded dataset.
              </p>
            </Card>
          </div>
        </>
      )}
    </>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, ShieldAlert } from 'lucide-react'
import { PageHeader, Button, Card, ErrorState, PageSkeleton, StatCard, Table, useToast } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Callout, ChipGroup, Gate, RiskBadge, Slider } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { downloadCsv } from '../lib/csv'
import { useAppState } from '../lib/appstate'
import { useAsync, useDebounced } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'
import { RISK_COLOR, RISK_HEX, RISK_ORDER, shortBand } from '../lib/risk'

export default function Risk() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Customers"
        icon={ShieldAlert}
        title="Customer risk segmentation"
        lead="Every customer is scored and placed in a Low, Medium, High or Critical band. The band boundaries are yours to set."
      />
      <Gate need="model">
        <RiskBody />
      </Gate>
    </div>
  )
}

function RiskBody() {
  const toast = useToast()
  const { state, refresh } = useAppState()
  const [t, setT] = useState(state?.thresholds || { low: 30, medium: 60, high: 80 })
  const dt = useDebounced(t, 450)
  const [saveError, setSaveError] = useState('')
  const [bands, setBands] = useState(RISK_ORDER)
  const { data, error, loading, reload } = useAsync(() => api.risk(), [])

  // Persist thresholds (debounced) and re-score the table with the new bands.
  useEffect(() => {
    const cur = state?.thresholds
    if (!cur || (cur.low === dt.low && cur.medium === dt.medium && cur.high === dt.high)) return
    let alive = true
    api
      .saveThresholds(dt)
      .then(async () => {
        if (!alive) return
        setSaveError('')
        await refresh()
        reload()
      })
      .catch((e) => alive && setSaveError(e.message))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dt])

  const setLow = (low) => setT((p) => ({ low, medium: Math.max(p.medium, low + 5), high: Math.max(p.high, Math.max(p.medium, low + 5) + 5) }))
  const setMedium = (medium) => setT((p) => ({ ...p, medium, high: Math.max(p.high, medium + 5) }))
  const setHigh = (high) => setT((p) => ({ ...p, high }))

  const rows = useMemo(() => (data ? data.rows.filter((r) => bands.includes(r.risk_category)) : []), [data, bands])

  const exportCsv = () => {
    downloadCsv('customer_risk_table.csv', rows)
    toast({ kind: 'success', title: 'CSV downloaded', message: `${fmtInt(rows.length)} customers exported.` })
  }

  if (error && !data) return <ErrorState title="Risk table could not load" error={error} onRetry={reload} />
  if (!data) return <PageSkeleton kpis={5} blocks={1} />
  const s = data.summary

  return (
    <>
      <Card title="Risk threshold configuration" subtitle="Application-defined bands on the predicted churn probability, not universal cut-offs. Adjust them to fit your business.">
        <div className="stack" style={{ '--gap': '20px' }}>
          <div className="form-grid wide">
            <Slider id="th-low" label="Low / Medium boundary" value={t.low} min={5} max={50} onChange={setLow} format={(v) => `${v}%`} />
            <Slider id="th-med" label="Medium / High boundary" value={t.medium} min={t.low + 5} max={85} onChange={setMedium} format={(v) => `${v}%`} />
            <Slider id="th-high" label="High / Critical boundary" value={t.high} min={t.medium + 5} max={95} onChange={setHigh} format={(v) => `${v}%`} />
          </div>
          <div>
            <div className="band-scale" role="img" aria-label={`Low below ${t.low} percent, Medium to ${t.medium}, High to ${t.high}, Critical above`}>
              {[t.low, t.medium - t.low, t.high - t.medium, 100 - t.high].map((w, i) => (
                <div key={i} style={{ flexGrow: w, background: RISK_COLOR[RISK_ORDER[i]] }} />
              ))}
            </div>
            <div className="band-legend">
              <span>0%</span>
              <span>Low &lt; {t.low}%</span>
              <span>Medium &lt; {t.medium}%</span>
              <span>High &lt; {t.high}%</span>
              <span>Critical ≥ {t.high}%</span>
              <span>100%</span>
            </div>
          </div>
          {saveError && (
            <Callout tone="error" title="Thresholds not saved">
              {saveError}
            </Callout>
          )}
        </div>
      </Card>

      <div style={{ opacity: loading ? 0.65 : 1, transition: 'opacity .2s' }} aria-busy={loading} className="stack">
        <Stagger className="grid-kpi">
          <Stagger.Item><StatCard label="Total customers" value={s.total} format={fmtInt} tone="lavender" foot={`Avg. probability ${fmtNum(s.avg_probability, 1)}%`} /></Stagger.Item>
          {RISK_ORDER.map((b, i) => (
            <Stagger.Item key={b}>
              <StatCard label={b} value={s.counts[b] || 0} format={fmtInt} tone={['mint', 'sky', 'peach', 'rose'][i]} foot={`${s.percentages[b] ?? 0}% of customers`} />
            </Stagger.Item>
          ))}
        </Stagger>

        <Card title="Customers per risk band">
          <BarCompare label="Customer count by risk band" data={RISK_ORDER.map((b) => ({ name: shortBand(b), value: s.counts[b] || 0, color: RISK_HEX[b] }))} valueFormat={fmtInt} name="Customers" height={260} />
        </Card>

        <Card
          title="At-risk customer table"
          subtitle={`Showing ${fmtInt(rows.length)} of ${fmtInt(data.total)} customers, highest probability first.`}
          actions={
            <Button size="sm" variant="secondary" icon={Download} onClick={exportCsv} disabled={!rows.length}>
              Download CSV
            </Button>
          }
        >
          <Table
            caption="Customers by churn risk"
            pageSize={12}
            tall
            rowKey={(r) => r.customerID}
            cardTitle={(r) => r.customerID}
            searchKeys={['customerID']}
            searchPlaceholder="Search customer ID"
            initialSort={{ key: 'churn_probability', dir: 'desc' }}
            tools={<ChipGroup label="Risk bands" options={RISK_ORDER.map((b) => ({ value: b, label: shortBand(b) }))} value={bands} onChange={setBands} />}
            columns={[
              { key: 'customerID', label: 'Customer', render: (r) => <Link className="link-cell" to={`/app/customer?id=${encodeURIComponent(r.customerID)}`}>{r.customerID}</Link> },
              {
                key: 'churn_probability',
                label: 'Churn probability',
                numeric: true,
                render: (r) => (
                  <span className="prob-cell">
                    <span className="bar-track" aria-hidden="true">
                      <span className="bar-fill" style={{ display: 'block', width: `${r.churn_probability}%`, background: RISK_COLOR[r.risk_category] }} />
                    </span>
                    <span className="num">{fmtNum(r.churn_probability, 1)}%</span>
                  </span>
                ),
              },
              { key: 'risk_category', label: 'Risk', render: (r) => <RiskBadge band={r.risk_category} />, sortValue: (r) => RISK_ORDER.indexOf(r.risk_category) },
              { key: 'Contract', label: 'Contract' },
              { key: 'tenure', label: 'Tenure (mo)', numeric: true },
              { key: 'MonthlyCharges', label: 'Monthly charges', numeric: true, render: (r) => (r.MonthlyCharges == null ? '–' : fmtNum(r.MonthlyCharges, 2)) },
              { key: 'InternetService', label: 'Internet' },
              { key: 'PaymentMethod', label: 'Payment' },
            ]}
            rows={rows}
          />
        </Card>
      </div>
    </>
  )
}

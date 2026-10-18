import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Inbox, Lightbulb } from 'lucide-react'
import { PageHeader, Button, Card, EmptyState, ErrorState, Input, PageSkeleton, Table, useToast } from '../components/ui'
import { Callout, ChipGroup, Gate, RiskBadge } from '../components/app'
import { api } from '../lib/api'
import { downloadCsv } from '../lib/csv'
import { useAsync, useDebounced } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'
import { RISK_ORDER, shortBand } from '../lib/risk'

const RULES = [
  ['High risk + month-to-month contract', 'Consider offering a longer-term contract option with an incentive.'],
  ['High risk + no technical support', 'Consider proactive tech-support outreach or a limited free trial.'],
  ['High risk + no online security', 'Consider highlighting the online security add-on in a retention conversation.'],
  ['High monthly charges + high risk', 'Review plan fit against usage and present lower-cost alternatives.'],
  ['Electronic check payment + high risk', 'Review the payment experience and offer a smoother automatic option.'],
  ['Very new customer (6 months or less) + high risk', 'Run an early-lifecycle onboarding check-in.'],
  ['Fiber optic customer at elevated risk', 'Run a service-quality and satisfaction check-in.'],
  ['Low engagement with streaming add-ons', 'Offer a promotional trial to raise engagement and perceived value.'],
  ['Overall risk in the Critical band', 'Prioritise for a direct retention conversation with a case-specific offer.'],
]

export default function Retention() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Customers"
        icon={Lightbulb}
        title="Retention recommendations"
        lead="Suggested actions come from a local, rule-based engine. They are phrased as options to consider, never guarantees, and no external AI service is involved."
      />
      <Gate need="model">
        <Body />
      </Gate>
    </div>
  )
}

function Body() {
  const toast = useToast()
  const [bands, setBands] = useState(['High Risk', 'Critical Risk'])
  const [limit, setLimit] = useState(50)
  const dBands = useDebounced(bands, 250)
  const dLimit = useDebounced(limit, 450)
  const lim = Math.max(5, Math.min(500, Number(dLimit) || 50))
  const { data, loading, error, reload } = useAsync(() => api.retention(dBands.join(','), lim), [dBands.join(','), lim])

  const exportCsv = () => {
    downloadCsv('retention_recommendations.csv', data.rows)
    toast({ kind: 'success', title: 'CSV downloaded', message: `${fmtInt(data.rows.length)} suggestions exported.` })
  }

  return (
    <>
      <Card title="Filter customers" subtitle="Recommendations run per customer, so the limit keeps this screen quick on large datasets.">
        <div className="tool-row">
          <div className="field">
            <span className="field-label">Risk bands to include</span>
            <ChipGroup label="Risk bands" options={RISK_ORDER.map((b) => ({ value: b, label: shortBand(b) }))} value={bands} onChange={setBands} />
          </div>
          <Input id="limit" type="number" label="Max customers (5–500)" min={5} max={500} step={5} value={limit} onChange={(e) => setLimit(e.target.value)} style={{ maxWidth: 180 }} />
        </div>
      </Card>

      {error && !data ? (
        <ErrorState title="Recommendations could not load" error={error} onRetry={reload} />
      ) : !data ? (
        <PageSkeleton kpis={0} blocks={1} />
      ) : data.rows.length === 0 ? (
        <EmptyState
          icon={Inbox}
          title={bands.length ? 'No customers in those risk bands' : 'Pick at least one risk band'}
          message={bands.length ? `None of the ${fmtInt(data.available)} scored customers fall in the selected bands. Include more bands or adjust the thresholds on the Customer risk screen.` : 'Choose one or more bands above to generate suggestions.'}
          action={
            <Button variant="secondary" to="/app/risk">
              Adjust risk thresholds
            </Button>
          }
        />
      ) : (
        <Card
          title="Suggested actions"
          subtitle={`${fmtInt(data.customers)} customers · ${fmtInt(data.suggestions)} individual suggestions`}
          actions={
            <Button size="sm" variant="secondary" icon={Download} onClick={exportCsv}>
              Download CSV
            </Button>
          }
        >
          <div style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={loading}>
            <Table
              caption="Retention recommendations"
              pageSize={10}
              searchKeys={['customerID', 'reason', 'suggested_action']}
              searchPlaceholder="Search customer or action"
              rowKey={(r, i) => `${r.customerID}-${i}`}
              cardTitle={(r) => r.customerID}
              columns={[
                { key: 'customerID', label: 'Customer', render: (r) => <Link className="link-cell" to={`/app/customer?id=${encodeURIComponent(r.customerID)}`}>{r.customerID}</Link> },
                { key: 'churn_probability', label: 'Probability', numeric: true, render: (r) => `${fmtNum(r.churn_probability, 1)}%` },
                { key: 'risk_category', label: 'Risk', render: (r) => <RiskBadge band={r.risk_category} short /> },
                { key: 'reason', label: 'Why', wrap: true },
                { key: 'suggested_action', label: 'Suggested action', wrap: true },
              ]}
              rows={data.rows}
            />
          </div>
        </Card>
      )}

      <Card title="Recommendation rule reference" subtitle="The engine checks each customer against readable IF/THEN rules like these.">
        <div>
          {RULES.map(([when, then]) => (
            <div className="rule" key={when}>
              <b>{when}</b>
              <span className="muted">{then}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14 }}>
          <Callout tone="info">These rules run entirely locally in Python and do not call any external AI service.</Callout>
        </div>
      </Card>
    </>
  )
}

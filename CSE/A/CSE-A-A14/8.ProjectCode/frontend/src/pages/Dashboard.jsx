import { Link } from 'react-router-dom'
import { Database, Flame, Gauge, LayoutDashboard, RefreshCw, ShieldAlert, TrendingDown, Users } from 'lucide-react'
import { PageHeader, Button, Card, EmptyState, ErrorState, PageSkeleton, StatCard, Table } from '../components/ui'
import { BarCompare } from '../components/charts'
import { DonutChart } from '../components/charts/extra'
import { Callout, LoadSampleButton, QuickStartButton, RiskBadge } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useStateKey } from '../lib/appstate'
import { useAsync } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'
import { RISK_HEX, RISK_ORDER, shortBand } from '../lib/risk'

const pct = (v) => `${v}%`

export default function Dashboard() {
  const key = useStateKey()
  const { data: d, loading, error, reload } = useAsync(() => api.dashboard(), [key])

  return (
    <div className="stack">
      <PageHeader
        eyebrow="Overview"
        icon={LayoutDashboard}
        title="Retention dashboard"
        lead="Where churn risk sits today, which customers need attention first and what drives it."
        actions={
          <Button variant="secondary" icon={RefreshCw} onClick={reload} loading={loading && Boolean(d)}>
            Refresh
          </Button>
        }
      />

      {error && !d ? (
        <ErrorState title="The dashboard could not load" error={error} onRetry={reload} />
      ) : !d ? (
        <PageSkeleton kpis={5} blocks={2} />
      ) : d.stage === 'no_data' ? (
        <EmptyState
          icon={Database}
          title="Welcome - let's load some customers"
          message={
            d.model
              ? `A saved ${d.model.name} model was restored from disk, but there is no dataset in this session yet. Load one to score customers.`
              : 'Load the built-in sample (1,000 synthetic telecom customers) and this workspace trains a model for you in a few seconds, or upload your own CSV.'
          }
          action={
            <>
              {d.model ? <LoadSampleButton /> : <QuickStartButton />}
              <Button variant="secondary" to="/app/data" icon={Database}>
                Upload a CSV
              </Button>
            </>
          }
        />
      ) : (
        <Ready d={d} />
      )}
    </div>
  )
}

function Ready({ d }) {
  const k = d.kpis
  const ready = d.stage === 'ready'
  const dist = d.distribution.map((x) => ({ ...x, color: x.name === 'Churned' ? 'var(--rose)' : 'var(--mint)' }))
  const rows = d.at_risk || []
  return (
    <>
      <Stagger className="grid-kpi">
        <Stagger.Item>
          <StatCard label="Total customers" value={k.total_customers} format={fmtInt} icon={Users} tone="lavender" foot={d.dataset} />
        </Stagger.Item>
        <Stagger.Item>
          <StatCard label="Churn rate" value={k.churn_rate_pct} format={(v) => `${fmtNum(v, 1)}%`} icon={TrendingDown} tone="rose" foot={`${fmtInt(k.churned_customers)} churned`} />
        </Stagger.Item>
        {ready ? (
          <>
            <Stagger.Item>
              <StatCard label="High-risk customers" value={d.risk.counts['High Risk'] || 0} format={fmtInt} icon={ShieldAlert} tone="peach" foot="Probability in the High band" />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Critical-risk customers" value={d.risk.counts['Critical Risk'] || 0} format={fmtInt} icon={Flame} tone="rose" foot="Priority for outreach" />
            </Stagger.Item>
            <Stagger.Item>
              <StatCard label="Avg. churn probability" value={d.risk.avg_probability} format={(v) => `${fmtNum(v, 1)}%`} icon={Gauge} tone="sky" foot={d.model?.name} />
            </Stagger.Item>
          </>
        ) : (
          <Stagger.Item>
            <StatCard label="Avg. tenure" value={k.avg_tenure ?? null} format={(v) => `${fmtNum(v, 1)} mo`} icon={Gauge} tone="sky" />
          </Stagger.Item>
        )}
      </Stagger>

      {!ready && (
        <Callout tone="info" title="Train a model to unlock risk scoring">
          Risk bands, at-risk customers and churn drivers appear once a model is saved.{' '}
          <Link className="link-cell" to="/app/train">
            Open Model training
          </Link>{' '}
          or press Quick start.
          <div style={{ marginTop: 10 }}>
            <QuickStartButton size="sm">Quick start</QuickStartButton>
          </div>
        </Callout>
      )}

      <div className="grid-2">
        <Card title="Churn split" subtitle="Share of customers who churned in the dataset">
          <DonutChart data={dist} centerValue={`${fmtNum(k.churn_rate_pct, 1)}%`} centerLabel="churned" label="Churned versus retained customers" />
        </Card>
        {ready ? (
          <Card title="Risk distribution" subtitle="Customers per risk band at your current thresholds">
            <BarCompare
              label="Customers per risk band"
              data={RISK_ORDER.map((b) => ({ name: shortBand(b), value: d.risk.counts[b] || 0, color: RISK_HEX[b] }))}
              valueFormat={fmtInt}
              name="Customers"
            />
          </Card>
        ) : (
          d.by_contract && (
            <Card title="Churn rate by contract" subtitle="Share of each contract type that churned">
              <BarCompare label="Churn rate by contract" data={d.by_contract.map((r) => ({ name: r.name, value: r.rate }))} valueFormat={pct} name="Churn rate" />
            </Card>
          )
        )}
      </div>

      <div className="grid-2">
        {ready && d.by_contract && (
          <Card title="Churn rate by contract" subtitle="Month-to-month customers usually churn most">
            <BarCompare label="Churn rate by contract" data={d.by_contract.map((r) => ({ name: r.name, value: r.rate, highlight: r === d.by_contract[0] }))} valueFormat={pct} name="Churn rate" />
          </Card>
        )}
        {d.by_tenure && (
          <Card title="Churn rate by tenure" subtitle="Newer customers are the most fragile">
            <BarCompare label="Churn rate by tenure group" data={d.by_tenure.map((r) => ({ name: r.name, value: r.rate }))} valueFormat={pct} color="var(--mint)" name="Churn rate" />
          </Card>
        )}
      </div>

      {ready && d.drivers?.rows?.length > 0 && (
        <Card title="Top churn drivers" subtitle={`${d.drivers.label} · computed on the ${d.drivers.basis}`}>
          <BarCompare
            horizontal
            height={Math.max(260, d.drivers.rows.length * 34)}
            label="Top churn drivers"
            data={d.drivers.rows.map((r) => ({ name: r.label, value: Number(r.importance.toFixed(4)) }))}
            valueFormat={(v) => fmtNum(v, 3)}
            yWidth={190}
            color="var(--lavender)"
            name="Importance"
          />
        </Card>
      )}

      {ready && (
        <Card title="Customers most at risk" subtitle="Top 20 by predicted churn probability" actions={<Button size="sm" variant="secondary" to="/app/risk">See all customers</Button>}>
          <Table
            caption="Top 20 at-risk customers"
            pageSize={10}
            rowKey={(r) => r.customerID}
            cardTitle={(r) => r.customerID}
            columns={[
              { key: 'customerID', label: 'Customer', render: (r) => <Link className="link-cell" to={`/app/customer?id=${encodeURIComponent(r.customerID)}`}>{r.customerID}</Link> },
              {
                key: 'churn_probability',
                label: 'Churn probability',
                numeric: true,
                render: (r) => <span className="num">{fmtNum(r.churn_probability, 1)}%</span>,
              },
              { key: 'risk_category', label: 'Risk', render: (r) => <RiskBadge band={r.risk_category} /> },
              { key: 'Contract', label: 'Contract' },
              { key: 'tenure', label: 'Tenure (mo)', numeric: true },
              { key: 'MonthlyCharges', label: 'Monthly charges', numeric: true, render: (r) => (r.MonthlyCharges == null ? '–' : fmtNum(r.MonthlyCharges, 2)) },
            ]}
            rows={rows}
          />
        </Card>
      )}
    </>
  )
}

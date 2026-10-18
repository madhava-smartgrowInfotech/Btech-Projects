import { useMemo, useState } from 'react'
import { Compass, Filter, X } from 'lucide-react'
import { PageHeader, Button, Card, ErrorState, PageSkeleton, Select, StatCard, Tabs } from '../components/ui'
import { BarCompare } from '../components/charts'
import { DonutChart, OverlayArea } from '../components/charts/extra'
import { Callout, ChipGroup, Gate, HeatGrid } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useAsync, useDebounced } from '../lib/hooks'
import { fmtInt, fmtNum } from '../lib/format'

const KPI_FMT = {
  total_customers: (v) => fmtInt(v),
  churned_customers: (v) => fmtInt(v),
  retained_customers: (v) => fmtInt(v),
  churn_rate_pct: (v) => `${fmtNum(v, 2)}%`,
  avg_tenure: (v) => `${fmtNum(v, 1)} mo`,
  avg_monthly_charges: (v) => fmtNum(v, 2),
  avg_total_charges: (v) => fmtNum(v, 2),
}
const KPI_TONE = ['lavender', 'rose', 'mint', 'peach', 'sky', 'lavender', 'mint']
const pct = (v) => `${v}%`

export default function Explore() {
  return (
    <div className="stack">
      <PageHeader eyebrow="Data" icon={Compass} title="Exploratory analysis" lead="Slice the prepared dataset and see where churn concentrates, by contract, service, tenure, charges and more." />
      <Gate need="data">
        <ExploreBody />
      </Gate>
    </div>
  )
}

function ExploreBody() {
  const [filters, setFilters] = useState({})
  const [numeric, setNumeric] = useState()
  const [tab, setTab] = useState()
  const [adding, setAdding] = useState('')
  const dFilters = useDebounced(filters, 300)
  const { data: d, loading, error, reload } = useAsync(() => api.eda(dFilters, numeric), [JSON.stringify(dFilters), numeric])

  const options = d?.filter_options || {}
  const available = useMemo(() => Object.keys(options).filter((c) => !(c in filters)), [options, filters])
  const activeCols = Object.keys(filters)

  const addFilter = (col) => {
    if (!col) return
    setFilters((f) => ({ ...f, [col]: options[col].map(String) }))
    setAdding('')
  }

  if (error && !d) return <ErrorState title="Exploration could not load" error={error} onRetry={reload} />
  if (!d) return <PageSkeleton kpis={7} blocks={2} />

  const tabs = d.by_category ? Object.keys(d.by_category).map((c) => ({ id: c, label: c })) : []
  const cur = tab && tabs.some((t) => t.id === tab) ? tab : tabs[0]?.id

  return (
    <>
      <Card title="Filter the data" subtitle={`Showing ${d.filtered_rows.toLocaleString('en-IN')} of ${d.total_rows.toLocaleString('en-IN')} customers`} actions={<Filter size={20} aria-hidden="true" />}>
        <div className="stack" style={{ '--gap': '16px' }}>
          <div className="tool-row">
            <Select
              id="add-filter"
              label="Add an attribute filter"
              value={adding}
              onChange={(e) => addFilter(e.target.value)}
              options={[{ value: '', label: available.length ? 'Choose an attribute…' : 'All attributes are in use' }, ...available]}
              disabled={!available.length}
            />
            {activeCols.length > 0 && (
              <Button variant="ghost" icon={X} onClick={() => setFilters({})}>
                Clear all filters
              </Button>
            )}
          </div>
          {activeCols.map((col) => (
            <div key={col} className="stack" style={{ '--gap': '8px' }}>
              <div className="row between">
                <strong>{col}</strong>
                <Button size="sm" variant="ghost" icon={X} onClick={() => setFilters(({ [col]: _, ...rest }) => rest)} aria-label={`Remove ${col} filter`}>
                  Remove
                </Button>
              </div>
              <ChipGroup label={`Values for ${col}`} options={(options[col] || []).map((v) => ({ value: String(v), label: String(v) }))} value={filters[col]} onChange={(v) => setFilters((f) => ({ ...f, [col]: v }))} />
            </div>
          ))}
          {activeCols.length === 0 && <p className="section-note">No filters applied. Add one to compare segments, for example Contract = Month-to-month.</p>}
        </div>
      </Card>

      {d.empty ? (
        <Callout tone="warn" title="No customers match these filters">
          Deselect a value or clear the filters to see charts again.
        </Callout>
      ) : (
        <div className="stack" style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={loading}>
          <Stagger className="grid-kpi">
            {d.kpis.map((k, i) => (
              <Stagger.Item key={k.key}>
                <StatCard label={k.label} value={k.value} format={KPI_FMT[k.key] || fmtInt} tone={KPI_TONE[i % KPI_TONE.length]} />
              </Stagger.Item>
            ))}
          </Stagger>

          <div className="grid-2">
            <Card title="Churn distribution">
              <DonutChart
                data={d.distribution.map((x) => ({ ...x, color: x.name === 'Churned' ? 'var(--rose)' : 'var(--mint)' }))}
                centerValue={`${fmtNum(d.kpis.find((k) => k.key === 'churn_rate_pct')?.value, 1)}%`}
                centerLabel="churned"
                label="Churned versus retained"
              />
            </Card>
            {d.by_tenure && (
              <Card title="Churn rate by tenure group">
                <BarCompare label="Churn rate by tenure group" data={d.by_tenure.map((r) => ({ name: r.name, value: r.rate }))} valueFormat={pct} color="var(--mint)" name="Churn rate" />
              </Card>
            )}
          </div>

          {tabs.length > 0 && (
            <Card title="Churn rate by customer attribute" subtitle="Share of each group that churned. Bars sorted from highest to lowest.">
              <div className="stack" style={{ '--gap': '14px' }}>
                <Tabs tabs={tabs} value={cur} onChange={setTab} label="Attributes" name="eda-attr" />
                <BarCompare
                  label={`Churn rate by ${cur}`}
                  data={d.by_category[cur].map((r, i) => ({ name: r.name, value: r.rate, highlight: i === 0 }))}
                  valueFormat={pct}
                  name="Churn rate"
                />
                <p className="section-note">{d.by_category[cur].map((r) => `${r.name}: ${fmtInt(r.count)} customers`).join(' · ')}</p>
              </div>
            </Card>
          )}

          {d.histogram && (
            <Card
              title="Numeric feature distribution"
              subtitle="How retained and churned customers spread across one numeric feature"
              actions={<Select id="num" label="" aria-label="Numeric feature" value={d.numeric} onChange={(e) => setNumeric(e.target.value)} options={d.numeric_options} />}
            >
              <OverlayArea
                label={`Distribution of ${d.numeric} by churn`}
                data={d.histogram}
                series={[
                  { key: 'retained', name: 'Retained', color: '#A7E8C8' },
                  { key: 'churned', name: 'Churned', color: '#FFB8C6' },
                ]}
                xFormat={(v) => fmtNum(v, Math.abs(v) < 10 ? 1 : 0)}
              />
            </Card>
          )}

          {d.correlation && (
            <Card title="Correlation between numeric features" subtitle="Lavender is positive, peach is negative. Stronger colour means a stronger relationship.">
              <HeatGrid
                label="Correlation matrix of numeric features"
                xLabels={d.correlation.columns}
                yLabels={d.correlation.columns}
                matrix={d.correlation.matrix}
                format={(v) => v.toFixed(2)}
                tone="diverging"
                cell={64}
              />
            </Card>
          )}
        </div>
      )}
    </>
  )
}

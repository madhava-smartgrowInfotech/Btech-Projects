import { useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowDown, ArrowUp, Check, FlaskConical, Sparkles, UserRound } from 'lucide-react'
import { PageHeader, Badge, Button, Card, ErrorState, KeyValueList, PageSkeleton, Timeline } from '../components/ui'
import { Callout, CustomerPicker, FactorList, Gate, Gauge, RiskBadge } from '../components/app'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'

export default function Customer360() {
  return (
    <div className="stack">
      <PageHeader eyebrow="Customers" icon={UserRound} title="Customer 360° profile" lead="One consolidated view: who the customer is, how likely they are to leave, why, and what could be done." />
      <Gate need="model">
        <Body />
      </Gate>
    </div>
  )
}

function Body() {
  const [params, setParams] = useSearchParams()
  const id = params.get('id') || ''
  const setId = useCallback((v) => setParams(v ? { id: v } : {}, { replace: true }), [setParams])
  const { data: c, loading, error, reload } = useAsync(() => api.customer(id), [id], { enabled: Boolean(id) })

  return (
    <>
      <Card title="Find a customer" subtitle="Search by ID. The list is ordered with the highest churn risk first.">
        <CustomerPicker value={id} onChange={setId} />
      </Card>

      {!id ? (
        <PageSkeleton kpis={3} blocks={2} />
      ) : error && !c ? (
        <ErrorState title="Customer could not load" error={error} onRetry={reload} />
      ) : !c ? (
        <PageSkeleton kpis={3} blocks={2} />
      ) : (
        <div className="stack" style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={loading}>
          <div className="grid-2 wide-left">
            <Card>
              <div className="row between" style={{ alignItems: 'flex-start' }}>
                <div>
                  <span className="muted small">Customer</span>
                  <h2 style={{ fontSize: 26, marginTop: 4, overflowWrap: 'anywhere' }}>{c.id}</h2>
                  <div className="row" style={{ marginTop: 10 }}>
                    <RiskBadge band={c.risk} />
                    {c.tenure != null && <Badge tone="neutral">Tenure {c.tenure} months</Badge>}
                    {c.actual_churn != null && <Badge tone={c.actual_churn ? 'rose' : 'mint'}>Recorded outcome: {c.actual_churn ? 'churned' : 'retained'}</Badge>}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: 14 }}>
                <Gauge value={c.probability} band={c.risk} />
              </div>
            </Card>
            <Card title="Suggested retention actions" subtitle="Model-informed suggestions, not guarantees. Final decisions need human judgement.">
              <Timeline
                items={c.recommendations.map((r, i) => ({ id: i, title: r.suggestion, meta: `Reason: ${r.reason}`, icon: Check, tone: ['mint', 'lavender', 'peach', 'sky'][i % 4] }))}
              />
              <div className="row" style={{ marginTop: 18 }}>
                <Button size="sm" variant="secondary" icon={FlaskConical} to={`/app/whatif?id=${encodeURIComponent(c.id)}`}>
                  Test it in What-if
                </Button>
                <Button size="sm" variant="ghost" icon={Sparkles} to={`/app/explain?id=${encodeURIComponent(c.id)}`}>
                  Full explanation
                </Button>
              </div>
            </Card>
          </div>

          <div className="grid-2">
            <Card title="Top churn drivers" subtitle="Factors pushing this customer toward leaving">
              <FactorList items={c.drivers} tone="rose" icon={ArrowUp} empty="None identified." />
            </Card>
            <Card title="Protective factors" subtitle="Factors pulling this customer toward staying">
              <FactorList items={c.protective} tone="mint" icon={ArrowDown} empty="None identified." />
            </Card>
          </div>
          {c.method !== 'shap' && (
            <Callout tone="info" title="Approximate explanation">
              SHAP is not installed, so these factors use model importance multiplied by the customer’s feature values. Install <span className="code-pill">shap</span> for exact contributions.
            </Callout>
          )}

          <div className="grid-2">
            {c.groups.map((g) => (
              <Card key={g.name} title={g.name}>
                <KeyValueList items={g.items.map((i) => [i.label, i.value == null ? '–' : String(i.value)])} />
              </Card>
            ))}
          </div>
          <p className="section-note">
            Looking for several customers at once? Use the <Link className="link-cell" to="/app/risk">risk table</Link>.
          </p>
        </div>
      )}
    </>
  )
}

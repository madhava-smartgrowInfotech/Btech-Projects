import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowDown, ArrowUp, Globe2, Sparkles, UserRound } from 'lucide-react'
import { PageHeader, Badge, Card, ErrorState, PageSkeleton, Skeleton, StatCard, Tabs } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Callout, CustomerPicker, FactorList, Gate, RiskBadge } from '../components/app'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtNum } from '../lib/format'

export default function Explain() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Customers"
        icon={Sparkles}
        title="Explainable AI"
        lead="A global view of what drives churn across all customers, and a local view of why one specific customer received their score."
      />
      <Gate need="model">
        <Body />
      </Gate>
    </div>
  )
}

function Body() {
  return (
    <>
      <GlobalExplanation />
      <LocalExplanation />
    </>
  )
}

function GlobalExplanation() {
  const { data, error, reload } = useAsync(() => api.xaiGlobal(), [])
  const [tab, setTab] = useState()
  if (error && !data) return <ErrorState title="Global explanation unavailable" error={error} onRetry={reload} />
  if (!data) return <PageSkeleton kpis={0} blocks={1} />
  const methods = data.methods
  const cur = methods.find((m) => m.key === tab) || methods[0]
  return (
    <Card
      title="Global explanation"
      subtitle={`What generally influences ${data.model_name} across all customers · computed on the ${data.basis}`}
      actions={<Globe2 size={20} aria-hidden="true" />}
    >
      <div className="stack">
        {!data.shap_available && (
          <Callout tone="info" title="SHAP is not installed">
            Explanations use permutation importance and model coefficients instead of true SHAP values. Run <span className="code-pill">pip install shap</span> and restart the API for SHAP-based drivers.
          </Callout>
        )}
        {!methods.length ? (
          <Callout tone="warn">Could not compute global importance for this model.</Callout>
        ) : (
          <>
            <Tabs tabs={methods.map((m) => ({ id: m.key, label: m.label }))} value={cur.key} onChange={setTab} label="Importance method" name="xai-method" />
            <BarCompare
              horizontal
              height={Math.max(300, cur.rows.length * 34)}
              label={`Top churn drivers by ${cur.label}`}
              data={cur.rows.map((r, i) => ({ name: r.label, value: Number(r.importance.toFixed(4)), highlight: i < 3 }))}
              valueFormat={(v) => fmtNum(v, 3)}
              yWidth={200}
              color="var(--sky)"
              name={cur.label}
            />
          </>
        )}
      </div>
    </Card>
  )
}

function LocalExplanation() {
  const [params, setParams] = useSearchParams()
  const id = params.get('id') || ''
  const setId = useCallback((v) => setParams(v ? { id: v } : {}, { replace: true }), [setParams])
  const { data: d, loading, error, reload } = useAsync(() => api.xaiLocal(id), [id], { enabled: Boolean(id) })

  return (
    <Card title="Local explanation" subtitle="Why this specific customer received their score, not just the global pattern." actions={<UserRound size={20} aria-hidden="true" />}>
      <div className="stack">
        <CustomerPicker value={id} onChange={setId} label="Customer to explain" />
        {!id || (!d && !error) ? (
          <Skeleton height={200} radius={18} />
        ) : error && !d ? (
          <ErrorState compact title="Explanation unavailable" error={error} onRetry={reload} />
        ) : (
          <div className="stack" style={{ opacity: loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={loading}>
            <div className="grid-kpi">
              <StatCard label="Customer" display={d.id} tone="lavender" />
              <StatCard label="Churn probability" display={`${fmtNum(d.probability, 1)}%`} tone="rose" foot={<RiskBadge band={d.risk} />} />
            </div>
            <p className="small muted">
              Method: <Badge tone={d.method === 'shap' ? 'mint' : 'neutral'}>{d.method === 'shap' ? 'SHAP' : 'Approximate (importance × feature value)'}</Badge>
            </p>
            <div className="grid-2">
              <div>
                <h3 style={{ marginBottom: 12 }}>Main churn drivers</h3>
                <p className="section-note" style={{ marginBottom: 12 }}>Push toward churn</p>
                <FactorList items={d.drivers} tone="rose" icon={ArrowUp} empty="None identified." />
              </div>
              <div>
                <h3 style={{ marginBottom: 12 }}>Protective factors</h3>
                <p className="section-note" style={{ marginBottom: 12 }}>Push away from churn</p>
                <FactorList items={d.protective} tone="mint" icon={ArrowDown} empty="None identified." />
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

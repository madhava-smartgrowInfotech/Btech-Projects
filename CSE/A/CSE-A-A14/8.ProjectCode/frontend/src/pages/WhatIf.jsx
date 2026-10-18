import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowRight, FlaskConical, RotateCcw } from 'lucide-react'
import { PageHeader, Badge, Button, Card, ErrorState, PageSkeleton, Select, StatCard } from '../components/ui'
import { Callout, CustomerPicker, Gate, RiskBadge, Slider } from '../components/app'
import { CountUp } from '../components/motion'
import { api } from '../lib/api'
import { useAsync, useDebounced } from '../lib/hooks'
import { fmtNum } from '../lib/format'

export default function WhatIf() {
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Customers"
        icon={FlaskConical}
        title="What-if churn analysis"
        lead="Change a customer’s attributes and see how the trained model’s prediction responds. This is model-based scenario analysis; it does not claim the change would make the customer stay."
      />
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
  const schema = useAsync(() => api.whatifSchema(id), [id], { enabled: Boolean(id) })
  const [values, setValues] = useState({})

  const s = schema.data
  useEffect(() => {
    if (s?.current) setValues(s.current)
  }, [s])

  const changes = useMemo(() => {
    if (!s) return {}
    const out = {}
    s.fields.forEach((f) => {
      if (values[f.name] !== undefined && String(values[f.name]) !== String(s.current[f.name])) out[f.name] = values[f.name]
    })
    return out
  }, [s, values])
  const dChanges = useDebounced(changes, 300)
  const result = useAsync(() => api.whatif(id, dChanges), [id, JSON.stringify(dChanges), s?.customer], { enabled: Boolean(id && s) })

  const set = (name, v) => setValues((p) => ({ ...p, [name]: v }))
  const r = result.data
  const nChanged = Object.keys(changes).length

  return (
    <>
      <Card title="Starting point" subtitle="Pick the customer whose attributes you want to play with.">
        <CustomerPicker value={id} onChange={setId} label="Customer" />
      </Card>

      {!id || (!s && !schema.error) ? (
        <PageSkeleton kpis={3} blocks={1} />
      ) : schema.error && !s ? (
        <ErrorState title="Scenario inputs could not load" error={schema.error} onRetry={schema.reload} />
      ) : (
        <>
          <Card
            title="Current attributes vs. scenario"
            subtitle="Adjust anything below. Changed fields are marked."
            actions={
              <Button size="sm" variant="secondary" icon={RotateCcw} onClick={() => setValues(s.current)} disabled={!nChanged}>
                Reset to current
              </Button>
            }
          >
            <div className="form-grid wide">
              {s.fields.map((f) => {
                const changed = f.name in changes
                const label = (
                  <>
                    {f.name} {changed && <Badge tone="lavender">changed</Badge>}
                  </>
                )
                return f.type === 'numeric' ? (
                  <Slider
                    key={f.name}
                    id={`wi-${f.name}`}
                    label={label}
                    value={Number(values[f.name] ?? s.current[f.name] ?? f.min)}
                    min={f.min}
                    max={f.max}
                    step={f.step}
                    onChange={(v) => set(f.name, v)}
                    format={(v) => (Number.isInteger(f.step) ? v : fmtNum(v, 2))}
                  />
                ) : (
                  <Select
                    key={f.name}
                    id={`wi-${f.name}`}
                    label={label}
                    value={String(values[f.name] ?? s.current[f.name] ?? '')}
                    onChange={(e) => set(f.name, e.target.value)}
                    options={f.options}
                  />
                )
              })}
            </div>
          </Card>

          <Card title="Scenario result" subtitle="Updates as you change inputs">
            {result.error && !r ? (
              <ErrorState compact title="Could not score the scenario" error={result.error} onRetry={result.reload} />
            ) : !r ? (
              <PageSkeleton kpis={3} blocks={0} />
            ) : (
              <div className="stack" style={{ opacity: result.loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={result.loading}>
                <div className="grid-kpi">
                  <StatCard label="Original churn probability" value={r.original} format={(v) => `${fmtNum(v, 1)}%`} tone="lavender" foot={<RiskBadge band={r.original_risk} />} />
                  <StatCard label="Scenario churn probability" value={r.scenario} format={(v) => `${fmtNum(v, 1)}%`} tone="sky" foot={<RiskBadge band={r.scenario_risk} />} />
                  <StatCard
                    label="Change"
                    display={
                      <span className={`delta-big ${r.verdict === 'lower' ? 'down' : r.verdict === 'higher' ? 'up' : ''}`}>
                        {r.change > 0 ? '+' : r.change < 0 ? '−' : ''}
                        <CountUp value={Math.abs(r.change)} format={(v) => fmtNum(v, 1)} duration={0.6} /> pp
                      </span>
                    }
                    tone={r.verdict === 'lower' ? 'mint' : r.verdict === 'higher' ? 'rose' : 'peach'}
                    foot={nChanged ? `${nChanged} attribute${nChanged === 1 ? '' : 's'} changed` : 'No changes yet'}
                  />
                </div>
                {r.verdict === 'none' ? (
                  <Callout tone="info">{nChanged ? 'This scenario produces almost no change in predicted churn probability.' : 'Move a slider or choose a different option to build a scenario.'}</Callout>
                ) : r.verdict === 'lower' ? (
                  <Callout tone="success" title="Lower risk under this scenario">
                    The model’s predicted churn probability decreases by {fmtNum(Math.abs(r.change), 1)} percentage points{r.original_risk !== r.scenario_risk && <> and moves the customer from {r.original_risk} to {r.scenario_risk}</>}.
                  </Callout>
                ) : (
                  <Callout tone="warn" title="Higher risk under this scenario">
                    The model’s predicted churn probability increases by {fmtNum(r.change, 1)} percentage points{r.original_risk !== r.scenario_risk && <> and moves the customer from {r.original_risk} to {r.scenario_risk}</>}.
                  </Callout>
                )}
                <p className="section-note">
                  <strong>Model-based scenario analysis:</strong> shows how the model’s prediction changes under hypothetical attributes. It is not a causal guarantee of customer behaviour.
                </p>
                <div className="row">
                  <Button size="sm" variant="ghost" to={`/app/customer?id=${encodeURIComponent(id)}`} iconRight={ArrowRight}>
                    Open Customer 360
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </>
      )}
    </>
  )
}

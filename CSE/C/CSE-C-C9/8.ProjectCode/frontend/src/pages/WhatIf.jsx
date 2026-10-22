import { useState } from 'react'
import { AlertTriangle, ArrowRight, FlaskConical, Play, RotateCcw } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { loadBaseline, saveBaseline } from '../lib/baseline'
import { fmtSigned } from '../lib/format'
import { Badge, Button, Card, Input, PageHeader, Select, Skeleton, useToast } from '../components/ui'
import { CountUp, SlideUp } from '../components/motion'
import Async from '../components/Async'
import ProfileForm, { EMPTY_PROFILE, SAMPLE_PROFILE, validateProfile } from '../components/ProfileForm'
import { Disclaimer, FIELD_LABELS, ProfileBadge, RiskBadge } from '../components/Common'

const EMPTY_SCENARIO = { scenario_capital_gain: '', scenario_capital_loss: '', scenario_hours: '', scenario_education: '' }

function Side({ title, data, tint }) {
  return (
    <Card hover={false} tint={tint} title={title}>
      <div className="stack" style={{ '--gap': '12px' }}>
        <div className="row"><ProfileBadge profile={data.profile} /><RiskBadge risk={data.risk} /></div>
        <div>
          <span className="small muted">Financial-strength score</span>
          <div className="stat-value"><CountUp value={data.strength_pct} format={(v) => `${v.toFixed(1)}%`} /></div>
        </div>
      </div>
    </Card>
  )
}

function Results({ r }) {
  const dir = r.delta_pct > 0.5 ? 'mint' : r.delta_pct < -0.5 ? 'rose' : 'sky'
  const show = (v) => (typeof v === 'number' ? v.toLocaleString('en-US') : String(v))
  return (
    <SlideUp className="stack" style={{ '--gap': '18px' }} id="whatif-results">
      <div className="grid-2">
        <Side title="Baseline" data={r.baseline} />
        <Side title="Scenario" data={r.scenario} tint={dir} />
      </div>
      <Card hover={false} tint={dir} title="Comparison">
        <div className="stack" style={{ '--gap': '12px' }}>
          <p>
            Change in score: <strong className="num">{fmtSigned(r.delta_pct, 2, ' percentage points')}</strong>
          </p>
          <p>{r.verdict}</p>
          {r.changed.length > 0 && (
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {r.changed.map((c) => (
                <li key={c.field}>
                  <strong>{FIELD_LABELS[c.field] || c.field}:</strong> {show(c.from)} → {show(c.to)}
                </li>
              ))}
            </ul>
          )}
          <div className="row">
            {r.profile_changed && <Badge tone="lavender">Profile changed: {r.baseline.profile} → {r.scenario.profile}</Badge>}
            {r.risk_changed && <Badge tone="peach">Risk band changed: {r.baseline.risk} → {r.scenario.risk}</Badge>}
            {!r.profile_changed && !r.risk_changed && <Badge tone="neutral">Profile and risk band unchanged</Badge>}
          </div>
        </div>
      </Card>
    </SlideUp>
  )
}

function WhatIfForm({ options }) {
  const toast = useToast()
  const [values, setValues] = useState(() => ({ ...EMPTY_PROFILE, ...(loadBaseline() || {}) }))
  const [scenario, setScenario] = useState(EMPTY_SCENARIO)
  const [errors, setErrors] = useState({})
  const [serverErrors, setServerErrors] = useState([])
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const fromAssessment = !!loadBaseline()

  const setS = (k) => (e) => setScenario({ ...scenario, [k]: e.target.value })
  const submit = async (e) => {
    e.preventDefault()
    const errs = validateProfile(values, options)
    setErrors(errs)
    setServerErrors([])
    if (Object.keys(errs).length) {
      setServerErrors(['Please fix the highlighted baseline fields.'])
      document.querySelector('[aria-invalid="true"]')?.focus()
      return
    }
    if (!Object.values(scenario).some((v) => String(v).trim() !== '')) {
      setServerErrors(['Change at least one scenario field to compare.'])
      return
    }
    setBusy(true)
    try {
      const r = await api.whatif({ ...values, ...scenario })
      saveBaseline(values)
      setResult(r)
      toast({ kind: 'success', title: 'Scenario compared', message: `Score change ${fmtSigned(r.delta_pct, 2, ' pp')}.` })
      setTimeout(() => document.getElementById('whatif-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120)
    } catch (err) {
      setResult(null)
      setServerErrors(err.errors?.length ? err.errors : [err.message])
      toast({ kind: 'error', title: 'Scenario failed', message: err.status === 0 ? 'The API is offline.' : 'Check the inputs and try again.' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '18px' }}>
        {serverErrors.length > 0 && (
          <div className="state error" role="alert" style={{ alignItems: 'flex-start', textAlign: 'left', padding: '18px 20px' }}>
            <strong className="row" style={{ '--gap': '8px' }}><AlertTriangle size={18} aria-hidden="true" />Could not run the scenario</strong>
            <ul style={{ margin: 0, paddingLeft: 20 }}>{serverErrors.map((m) => <li key={m}>{m}</li>)}</ul>
          </div>
        )}
        <Card hover={false} title="Baseline information" subtitle={fromAssessment ? 'Pre-filled from your last assessment.' : 'Enter a baseline, or load the sample profile.'}
          actions={<>
            <Button variant="ghost" size="sm" onClick={() => { setValues(SAMPLE_PROFILE); setErrors({}) }}>Use sample profile</Button>
            <Button variant="ghost" size="sm" icon={RotateCcw} onClick={() => { setValues(EMPTY_PROFILE); setScenario(EMPTY_SCENARIO); setErrors({}); setResult(null); setServerErrors([]) }}>Clear</Button>
          </>}>
          <ProfileForm values={values} onChange={setValues} errors={errors} options={options} prefix="wi" />
        </Card>
        <Card hover={false} tint="lavender" title="Scenario changes" subtitle="Leave a field blank to keep the baseline value. Change at least one.">
          <div className="form-grid">
            <Input id="wi-sg" label="Scenario gains ($)" type="number" inputMode="numeric" min={0} max={1000000} hint="0 to 1,000,000" value={scenario.scenario_capital_gain} onChange={setS('scenario_capital_gain')} />
            <Input id="wi-sl" label="Scenario losses ($)" type="number" inputMode="numeric" min={0} max={1000000} hint="0 to 1,000,000" value={scenario.scenario_capital_loss} onChange={setS('scenario_capital_loss')} />
            <Input id="wi-sh" label="Scenario hours per week" type="number" inputMode="numeric" min={1} max={99} hint="1 to 99" value={scenario.scenario_hours} onChange={setS('scenario_hours')} />
            <Select id="wi-se" label="Scenario education" value={scenario.scenario_education} onChange={setS('scenario_education')} options={[{ value: '', label: 'Keep baseline…' }, ...options.education]} />
          </div>
        </Card>
        <div className="row">
          <Button type="submit" size="lg" icon={Play} loading={busy}>Compare scenarios</Button>
        </div>
      </form>
      {result && <Results r={result} />}
      <Disclaimer>This is a model what-if simulation, not a causal prediction. Informational estimates only, not financial advice.</Disclaimer>
    </div>
  )
}

export default function WhatIf() {
  const state = useAsync(api.options)
  return (
    <div className="stack" style={{ '--gap': '8px' }}>
      <PageHeader
        eyebrow="What-if"
        icon={FlaskConical}
        title="What-if financial scenario"
        lead="Enter a baseline, then change one or more scenario fields. The trained model re-runs on both and compares them side by side."
      />
      <Async state={state} title="Could not load the form options" skeleton={<div className="card"><Skeleton height={320} radius={18} /></div>}>
        {(options) => <WhatIfForm options={options} />}
      </Async>
    </div>
  )
}

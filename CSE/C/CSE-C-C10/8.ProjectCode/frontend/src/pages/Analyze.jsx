import { ArrowLeft, ListChecks, Sparkles, Wand2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { describeError, predict, useApi } from '../api'
import { Donut } from '../components/charts/Charts'
import { SlideUp } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import Table from '../components/ui/Table'
import { Button, Checkbox, Input, Select, Textarea } from '../components/ui/controls'
import { Badge, Card, KeyValueList, ScoreBar } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, Skeleton, useToast } from '../components/ui/feedback'
import { FIELD_LABELS, FLAG_LABELS, outcomeTone, pct, usd } from '../format'
import { logEvent } from '../lib/activity'
import { useTheme } from '../lib/theme'

const NUMERIC_GROUPS = {
  traction: ['funding_total_usd', 'funding_rounds', 'relationships', 'milestones', 'avg_participants'],
  timeline: ['age_first_funding_year', 'age_last_funding_year', 'age_first_milestone_year', 'age_last_milestone_year'],
}

// A starting point the user can edit; it is an example input, not data from the dataset.
const EXAMPLE = {
  industry_type: 'Software', state: 'CA', funding_total_usd: 2500000, funding_rounds: 2, relationships: 6, milestones: 3,
  has_VC: true, has_roundA: true,
  description: 'A subscription analytics platform for small retailers using demand forecasting, with 40 paying stores and growing monthly revenue.',
}

function initialValues(cfg) {
  const v = { industry_type: cfg.industries[0], state: cfg.states[0], k: cfg.default_k, description: '' }
  Object.entries(cfg.fields).forEach(([k, f]) => { v[k] = f.default })
  Object.keys(FLAG_LABELS).forEach((k) => { v[k] = false })
  return v
}

function validate(v, cfg) {
  const errs = {}
  Object.entries(cfg.fields).forEach(([k, f]) => {
    const n = Number(v[k])
    if (v[k] === '' || Number.isNaN(n)) errs[k] = 'Enter a number.'
    else if (n < f.min || n > f.max) errs[k] = `Between ${f.min.toLocaleString('en-US')} and ${f.max.toLocaleString('en-US')}.`
  })
  if (!v.description.trim()) errs.description = 'Describe the startup in a few sentences: product, market, business model, traction.'
  else if (v.description.length > cfg.max_description) errs.description = `Keep it under ${cfg.max_description} characters.`
  return errs
}

function PredictForm({ cfg, values, setValues, onSubmit, busy, error, errors }) {
  const set = (k) => (e) => setValues((v) => ({ ...v, [k]: e.target.value }))
  const num = (k) => (
    <Input key={k} id={k} label={FIELD_LABELS[k]} type="number" inputMode="decimal" value={values[k]} onChange={set(k)}
      min={cfg.fields[k].min} max={cfg.fields[k].max} step={cfg.fields[k].step} error={errors[k]} />
  )
  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Funding & traction" eyebrow="structured signals">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{NUMERIC_GROUPS.traction.map(num)}</div>
        </Card>
        <Card title="Company profile" eyebrow="structured signals">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {NUMERIC_GROUPS.timeline.map(num)}
            <Select label="Industry" value={values.industry_type} onChange={set('industry_type')} options={cfg.industries.map((x) => [x, x])} />
            <Select label="State" value={values.state} onChange={set('state')} options={cfg.states.map((x) => [x, x])} />
            <Select label="Comparable cases (k)" value={values.k} onChange={set('k')} options={cfg.ks.map((x) => [x, String(x)])} />
          </div>
        </Card>
      </div>

      <Card title="Investor signals" eyebrow="structured signals">
        <fieldset>
          <legend className="sr-only">Investor signals</legend>
          <div className="flex flex-wrap gap-x-6 gap-y-3">
            {Object.entries(FLAG_LABELS).map(([k, label]) => (
              <Checkbox key={k} label={label} checked={values[k]} onChange={(c) => setValues((v) => ({ ...v, [k]: c }))} />
            ))}
          </div>
        </fieldset>
      </Card>

      <Card title="Startup description" eyebrow="text signal">
        <Textarea id="description" label="Describe product, market, business model, technology and traction" rows={6} maxLength={cfg.max_description}
          value={values.description} onChange={set('description')} error={errors.description}
          placeholder="e.g. A subscription analytics platform for small retailers using demand forecasting, with 40 paying stores and growing monthly revenue…"
          hint={`${values.description.length} / ${cfg.max_description} characters · all processing happens locally on this server`} />
      </Card>

      <ErrorState error={error} title="Prediction failed" />
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" size="lg" loading={busy} icon={Sparkles}>Predict startup success</Button>
        <Button variant="secondary" size="lg" icon={Wand2} onClick={() => setValues((v) => ({ ...v, ...EXAMPLE }))} disabled={busy}>Fill an example</Button>
        <Button variant="ghost" size="lg" onClick={() => setValues(initialValues(cfg))} disabled={busy}>Reset</Button>
      </div>
    </form>
  )
}

function Result({ result, inputs, onBack }) {
  const { tokens } = useTheme()
  const ok = result.outcome === 'SUCCESS'
  const tone = outcomeTone(result.outcome)
  const cols = [
    { key: 'similarity', label: 'Similarity', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums">{r.similarity.toFixed(3)}</span> },
    { key: 'outcome', label: 'Outcome', sortable: true, defaultDir: 'asc', render: (r) => <Badge tone={outcomeTone(r.outcome)}>{r.outcome}</Badge> },
    { key: 'industry', label: 'Industry', sortable: true, defaultDir: 'asc' },
    { key: 'state', label: 'State', sortable: true, defaultDir: 'asc' },
    { key: 'funding_total_usd', label: 'Funding', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums">{usd(r.funding_total_usd)}</span> },
    { key: 'funding_rounds', label: 'Rounds', align: 'right', sortable: true, render: (r) => <span className="font-mono tabular-nums">{r.funding_rounds}</span> },
    { key: 'description', label: 'Summary', className: 'min-w-[260px] max-w-[420px] text-muted', render: (r) => <span className="line-clamp-2">{r.description}</span> },
  ]
  return (
    <SlideUp>
      <div className={`panel scan relative mb-5 overflow-hidden border-${tone}/40 p-5`} style={{ borderColor: `color-mix(in oklab, var(--${tone}) 45%, transparent)` }}>
        <div className="relative z-[1] flex flex-wrap items-center justify-between gap-5">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.16em] text-dim">estimated outcome</div>
            <div className="mt-1 font-mono text-4xl font-semibold tracking-tight sm:text-5xl" style={{ color: `var(--${tone})` }} role="status">{result.outcome}</div>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted">
              Confidence <b className="font-mono text-fg">{pct(result.confidence)}</b> · Model <b className="text-fg">{result.model}</b>
              <Badge tone={ok && result.confidence >= 0.7 ? 'ok' : result.confidence >= 0.55 ? 'warn' : 'alert'} dot>{result.risk}</Badge>
            </div>
          </div>
          <div className="w-full max-w-sm space-y-3">
            <ScoreBar value={result.probability_success} label="Success probability" tone={() => 'ok'} />
            <ScoreBar value={result.probability_failure} label="Failure probability" tone={() => 'alert'} />
          </div>
        </div>
        <p className="relative z-[1] mt-4 font-mono text-[11px] text-dim">This prediction is an analytical estimate, not a guarantee of future performance.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card title="Key contributing features" eyebrow="explanation" className="lg:col-span-2" action={<ListChecks size={14} className="text-ok" aria-hidden="true" />}>
          <ul className="space-y-2.5">
            {result.explanation.map((b) => (
              <li key={b} className="relative pl-4 text-sm text-muted before:absolute before:left-0 before:font-mono before:text-ok before:content-['›']">{b}</li>
            ))}
          </ul>
        </Card>
        <Card title="Evidence split" eyebrow={`k = ${result.k}`}>
          <Donut label="Outcomes of the retrieved comparable startups" height={190}
            data={[{ name: 'SUCCESS', value: result.similar_counts.SUCCESS, color: tokens.ok }, { name: 'FAILURE', value: result.similar_counts.FAILURE, color: tokens.alert }]}
            center={<div><div className="font-mono text-2xl font-semibold text-fg">{result.k}</div><div className="font-mono text-[10px] uppercase tracking-wider text-muted">cases</div></div>} />
        </Card>
      </div>

      <Card title={`Similar historical startups · k=${result.k} · ${result.similar_counts.SUCCESS} SUCCESS / ${result.similar_counts.FAILURE} FAILURE`} eyebrow="comparable cases" className="mt-5">
        <Table columns={cols} rows={result.similar} pageSize={10}
          initialSort={{ key: 'similarity', dir: 'desc' }} caption="Comparable historical startups"
          empty={<EmptyState title="No comparable startups" body="The retrieval step returned no records." />}
          cards={(r) => (
            <div className="rounded border border-line bg-panel-2 p-3 text-sm">
              <div className="mb-1 flex items-center justify-between">
                <Badge tone={outcomeTone(r.outcome)}>{r.outcome}</Badge>
                <span className="font-mono text-xs text-muted">sim {r.similarity.toFixed(3)}</span>
              </div>
              <div className="font-mono text-[11px] text-dim">{r.industry} · {r.state} · {usd(r.funding_total_usd)} · {r.funding_rounds} rounds</div>
              <p className="mt-1 line-clamp-3 text-xs text-muted">{r.description}</p>
            </div>
          )} />
      </Card>

      <Card title="Your inputs" eyebrow="submitted" className="mt-5">
        <KeyValueList cols={2} items={[
          ['Industry · State', `${inputs.industry_type} · ${inputs.state}`],
          ['Funding', `${usd(inputs.funding_total_usd)} across ${inputs.funding_rounds} rounds`],
          ['Relationships · Milestones', `${inputs.relationships} · ${inputs.milestones}`],
          ['Avg. participants', inputs.avg_participants],
          ['Investor signals', Object.keys(FLAG_LABELS).filter((k) => inputs[k]).map((k) => FLAG_LABELS[k]).join(', ') || 'none'],
          ['Comparable cases (k)', inputs.k],
        ]} />
        <p className="mt-3 border-t border-dashed border-line pt-3 text-sm text-muted">{inputs.description}</p>
      </Card>

      <div className="mt-6"><Button variant="secondary" icon={ArrowLeft} onClick={onBack}>Analyze another startup</Button></div>
    </SlideUp>
  )
}

export default function Analyze() {
  const { data: cfg, error: cfgError, loading, reload } = useApi('/config')
  const [values, setValues] = useState(null)
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [outcome, setOutcome] = useState(null) // { result, inputs }
  const toast = useToast()
  const top = useRef(null)

  useEffect(() => { if (cfg && !values) setValues(initialValues(cfg)) }, [cfg, values])
  const form = values

  if (cfgError) return <><PageHeader title="Analyze a startup" eyebrow="prediction" /><ErrorState error={cfgError} title="Could not load the form options" onRetry={reload} /></>
  if (loading || !cfg || !form) return <PageSkeleton />

  async function submit(e) {
    e.preventDefault()
    const errs = validate(form, cfg)
    setErrors(errs)
    if (Object.keys(errs).length) {
      setError({ message: 'Some values need attention.', hint: 'Fix the highlighted fields and submit again.' })
      document.getElementById(Object.keys(errs)[0])?.focus()
      return
    }
    setError(null)
    setBusy(true)
    const payload = {
      ...form, k: Number(form.k), description: form.description.trim(),
      ...Object.fromEntries(Object.keys(cfg.fields).map((k) => [k, Number(form[k])])),
    }
    try {
      const { data } = await predict(payload)
      logEvent('predict', `${data.outcome} · p(success) ${data.probability_success.toFixed(3)} · k=${data.k}`)
      toast({ tone: 'ok', title: `Estimated outcome: ${data.outcome}`, body: `Confidence ${pct(data.confidence)} · ${data.model}` })
      setOutcome({ result: data, inputs: payload })
      top.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } catch (err) {
      setError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div ref={top}>
      <PageHeader title={outcome ? 'Estimated startup outcome' : 'Analyze a startup'} eyebrow="prediction"
        subtitle={outcome ? 'Prediction, evidence and the comparable historical startups behind it.'
          : 'Enter what you know about the startup. All processing happens locally on this server.'} />
      {busy && !outcome && <div className="sr-only" role="status">Running the prediction</div>}
      {outcome ? (
        <Result result={outcome.result} inputs={outcome.inputs} onBack={() => setOutcome(null)} />
      ) : (
        <>
          <PredictForm cfg={cfg} values={form} setValues={setValues} onSubmit={submit} busy={busy} error={error} errors={errors} />
          {busy && <div className="mt-5 space-y-3" aria-hidden="true"><Skeleton className="h-24 w-full" /><Skeleton className="h-40 w-full" /></div>}
        </>
      )}
    </div>
  )
}

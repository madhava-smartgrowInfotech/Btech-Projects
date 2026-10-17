import { ChevronDown, ChevronUp, Play, RotateCcw, ShieldAlert, ShieldCheck, Zap } from 'lucide-react'
import { useState } from 'react'
import api, { describeError } from '../../api'
import { logEvent } from '../../lib/activity'
import { ADVANCED_FIELDS, buildRecord, initialForm, MAIN_FIELDS, PRESETS, PROTO, SERVICE, STATE } from '../../lib/features'
import { pushScored } from '../../lib/session'
import { pct } from '../../format'
import { Button, Input, Select } from '../ui/controls'
import { Badge, Card, ScoreBar, Severity } from '../ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../ui/feedback'

function ResultCard({ state, onRetry }) {
  const { loading, error, result } = state
  return (
    <Card title="Verdict" eyebrow="ensemble output" className="h-full" bodyClass="p-4">
      <div aria-live="polite" aria-busy={loading}>
        {loading && (
          <div className="space-y-3"><Skeleton className="h-9 w-40" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></div>
        )}
        {!loading && error && <ErrorState error={error} onRetry={onRetry} title="Scoring failed" />}
        {!loading && !error && !result && (
          <EmptyState icon={Zap} title="No record scored yet" body="Fill in the form and press Score record, or run one of the presets." />
        )}
        {!loading && !error && result && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              {result.label === 'attack'
                ? <ShieldAlert size={30} className="text-alert" aria-hidden="true" />
                : <ShieldCheck size={30} className="text-ok" aria-hidden="true" />}
              <div>
                <div className={`font-mono text-2xl font-semibold uppercase ${result.label === 'attack' ? 'text-alert' : 'text-ok'}`}>{result.label}</div>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-muted">severity <Severity s={result.severity} /></div>
              </div>
            </div>
            <ScoreBar value={result.confidence} label="Ensemble (stacked) probability of attack" />
            <ScoreBar value={result.xgb_score} label="XGBoost probability" />
            <ScoreBar value={result.cnn_score} label="1D CNN probability" />
            <p className="text-xs text-muted">
              Attack probability {pct(result.confidence)} - XGBoost {pct(result.xgb_score)} - CNN {pct(result.cnn_score)}.
              {result.alert && <> Logged to the <Badge tone="alert">alerts</Badge> list.</>}
            </p>
          </div>
        )}
      </div>
    </Card>
  )
}

export default function ScorePanel() {
  const toast = useToast()
  const [form, setForm] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [adv, setAdv] = useState(false)
  const [state, setState] = useState({ loading: false, error: null, result: null })
  const set = (k) => (e) => { setForm((f) => ({ ...f, [k]: e.target.value })); setErrors((x) => ({ ...x, [k]: undefined })) }

  async function submit(values = form) {
    const built = buildRecord(values)
    if (built.errors) {
      setErrors(built.errors)
      if (ADVANCED_FIELDS.some((f) => built.errors[f.key])) setAdv(true)
      toast({ tone: 'warn', title: 'Fix the highlighted fields', body: 'Every feature must be a non-negative number.' })
      return
    }
    setErrors({})
    setState({ loading: true, error: null, result: null })
    try {
      const { data } = await api.post('/ids/score', built.record)
      setState({ loading: false, error: null, result: data })
      pushScored({ source: 'single', label: data.label, confidence: data.confidence, severity: data.severity, proto: built.record.proto, service: built.record.service, state: built.record.state, xgb: data.xgb_score, cnn: data.cnn_score })
      logEvent('ids', `scored ${built.record.proto}/${built.record.service}/${built.record.state} -> ${data.label} ${pct(data.confidence)}`)
      toast(data.label === 'attack'
        ? { tone: 'alert', title: `Attack detected (${data.severity})`, body: `Attack probability ${pct(data.confidence)}.` }
        : { tone: 'ok', title: 'Traffic looks normal', body: `Attack probability ${pct(data.confidence)}.` })
    } catch (e) {
      setState({ loading: false, error: describeError(e), result: null })
    }
  }

  function preset(kind) {
    const next = { ...form, ...PRESETS[kind] }
    setForm(next)
    setErrors({})
    submit(next)
  }

  const numeric = (f) => (
    <Input key={f.key} label={f.label} type="number" inputMode="decimal" min="0" step={f.kind === 'int' ? '1' : 'any'}
      value={form[f.key]} onChange={set(f.key)} error={errors[f.key]} />
  )

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
      <Card title="Score a traffic record" eyebrow="POST /api/ids/score" className="lg:col-span-2"
        action={<Button variant="ghost" size="sm" icon={RotateCcw} onClick={() => { setForm(initialForm()); setErrors({}) }}>Reset</Button>}>
        <form onSubmit={(e) => { e.preventDefault(); submit() }} noValidate className="space-y-4">
          <p className="text-xs text-muted">
            Describe one network flow. Anything you leave in the advanced section keeps the API's defaults.
            The engine stacks XGBoost and a 1D CNN with logistic regression.
          </p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Select label="Protocol" options={PROTO} value={form.proto} onChange={set('proto')} />
            <Select label="Service" options={SERVICE} value={form.service} onChange={set('service')} />
            <Select label="State" options={STATE} value={form.state} onChange={set('state')} />
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{MAIN_FIELDS.map(numeric)}</div>

          <div>
            <button type="button" onClick={() => setAdv((v) => !v)} aria-expanded={adv} aria-controls="adv-fields"
              className="inline-flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-muted hover:text-fg">
              {adv ? <ChevronUp size={14} /> : <ChevronDown size={14} />}Advanced features ({ADVANCED_FIELDS.length})
            </button>
            {adv && (
              <div id="adv-fields" className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">{ADVANCED_FIELDS.map(numeric)}</div>
            )}
          </div>

          <div className="flex flex-wrap gap-2 border-t border-line pt-4">
            <Button type="submit" icon={Play} loading={state.loading}>Score record</Button>
            <Button variant="secondary" onClick={() => preset('normal')} disabled={state.loading}>Simulate normal</Button>
            <Button variant="danger" onClick={() => preset('attack')} disabled={state.loading}>Simulate attack</Button>
          </div>
        </form>
      </Card>
      <ResultCard state={state} onRetry={() => submit()} />
    </div>
  )
}

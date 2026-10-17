import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, Lightbulb, ScanSearch, ShieldAlert, ShieldCheck, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import { fmtPct } from '../lib/format'
import { softSpring } from '../lib/motion'
import { CHANNELS, MERCHANTS, MODE_CODE, MODE_LABEL, RISK_ACTION, RISK_TONE } from '../lib/labels'
import { Badge, Button, Card, EmptyState, ErrorState, Input, PageHeader, ProgressBar, Segmented, Select, Skeleton, useToast } from '../components/ui'
import RiskMeter from '../components/app/RiskMeter'

const PRESETS = {
  legit: { label: 'Everyday grocery purchase', Amount: '80', Merchant_Category: 'Grocery', Transaction_Type: 'Chip', Card_Present: '1', Country_Match: '1', Time: '54000', V3: '0', V14: '0', V17: '0' },
  fraud: { label: 'Large online purchase, abroad', Amount: '1200', Merchant_Category: 'Online', Transaction_Type: 'Online', Card_Present: '0', Country_Match: '0', Time: '54000', V3: '1.8', V14: '-1.1', V17: '1.4' },
}
const YES_NO = [
  { value: '1', label: 'Yes' },
  { value: '0', label: 'No' },
]
const MODE_OPTIONS = [
  { value: 'ensemble', label: 'Ensemble' },
  { value: 'classical', label: MODE_CODE.classical },
  { value: 'sa', label: MODE_CODE.sa },
  { value: 'qa', label: MODE_CODE.qa },
]
const NUMERIC = ['Amount', 'Time', 'V3', 'V14', 'V17']

// same bands the API uses for risk_level
const band = (p) => (p > 0.7 ? 'HIGH' : p > 0.4 ? 'MEDIUM' : 'LOW')

function validate(f) {
  const e = {}
  for (const k of NUMERIC) if (f[k] === '' || Number.isNaN(Number(f[k]))) e[k] = 'Enter a number.'
  if (!e.Amount && Number(f.Amount) < 0) e.Amount = 'Amount cannot be negative.'
  if (!e.Time && Number(f.Time) < 0) e.Time = 'Time cannot be negative.'
  return e
}

function Result({ res, mode }) {
  const fraud = res.prediction === 1
  const risk = res.risk_level || band(res.fraud_probability)
  return (
    <motion.div className="stack" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={softSpring} aria-live="polite">
      <div className="verdict">
        <span className="verdict-ico" style={{ background: fraud ? 'var(--rose)' : 'var(--mint)' }}>
          {fraud ? <ShieldAlert size={30} aria-hidden="true" /> : <ShieldCheck size={30} aria-hidden="true" />}
        </span>
        <div>
          <h2>{fraud ? 'Likely fraud' : 'Looks legitimate'}</h2>
          <p className="muted">{mode === 'ensemble' ? 'Average of all loaded models' : `${MODE_LABEL[mode]} model only`}</p>
        </div>
        <Badge tone={RISK_TONE[risk]} dot style={{ marginLeft: 'auto' }}>{risk} risk</Badge>
      </div>
      <div>
        <div className="row between" style={{ marginBottom: 12 }}>
          <span className="small muted">Fraud probability</span>
          <span className="big-num">{fmtPct(res.fraud_probability)}</span>
        </div>
        <RiskMeter probability={res.fraud_probability} />
      </div>
      <div className="notice info">
        <Lightbulb size={18} aria-hidden="true" />
        <span>
          <strong>Recommended action: {RISK_ACTION[risk]}.</strong> The headline verdict flips to fraud above 50%; the action bands are 40% and 70%.
        </span>
      </div>
      {res.individual_models && (
        <div className="stack" style={{ '--gap': '14px' }}>
          <h3>Per-model probability</h3>
          {Object.entries(res.individual_models).map(([m, p]) => (
            <div className="model-row" key={m}>
              <span>
                {MODE_LABEL[m]} <span className="muted tiny">({MODE_CODE[m]})</span>
              </span>
              <b className="num">{fmtPct(p)}</b>
              <ProgressBar value={p} tone={p > 0.7 ? 'rose' : p > 0.4 ? 'peach' : 'mint'} label={`${MODE_LABEL[m]} fraud probability`} />
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}

export default function Verify() {
  const toast = useToast()
  const [form, setForm] = useState(PRESETS.fraud)
  const [errors, setErrors] = useState({})
  const [mode, setMode] = useState('ensemble')
  const [state, setState] = useState({ status: 'idle', res: null, error: null, mode: 'ensemble' })

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e?.preventDefault()
    const errs = validate(form)
    setErrors(errs)
    if (Object.keys(errs).length) {
      toast({ kind: 'error', title: 'Check the form', message: 'Some fields need a valid number.' })
      return
    }
    setState((s) => ({ ...s, status: 'loading', error: null }))
    try {
      const res = await api.predictSingle({
        Amount: Number(form.Amount),
        Time: Number(form.Time),
        Merchant_Category: form.Merchant_Category,
        Transaction_Type: form.Transaction_Type,
        Card_Present: Number(form.Card_Present),
        Country_Match: Number(form.Country_Match),
        V3: Number(form.V3),
        V14: Number(form.V14),
        V17: Number(form.V17),
        mode,
      })
      setState({ status: 'done', res, error: null, mode })
      toast({ kind: 'success', title: res.prediction === 1 ? 'Flagged as likely fraud' : 'Looks legitimate', message: `Fraud probability ${fmtPct(res.fraud_probability)}` })
    } catch (error) {
      setState({ status: 'error', res: null, error, mode })
    }
  }

  const applyPreset = (key) => {
    setForm(PRESETS[key])
    setErrors({})
  }

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Single check"
        icon={ScanSearch}
        title="Verify a transaction"
        lead="Describe one payment and get an instant fraud probability from the trained models."
      />
      <div className="grid-2">
        <Card title="Transaction details" subtitle="Fields the models were trained on" hover={false}>
          <form className="stack" onSubmit={submit} noValidate>
            <div className="chip-row" role="group" aria-label="Fill with an example">
              <span className="small muted" style={{ alignSelf: 'center' }}>Try an example:</span>
              {Object.entries(PRESETS).map(([k, p]) => (
                <button type="button" key={k} className="chip-btn" onClick={() => applyPreset(k)}>
                  <Sparkles size={15} aria-hidden="true" />
                  {p.label}
                </button>
              ))}
            </div>
            <div className="form-grid">
              <Input label="Amount (USD)" type="number" inputMode="decimal" min="0" step="any" value={form.Amount} onChange={set('Amount')} error={errors.Amount} required />
              <Select label="Merchant category" value={form.Merchant_Category} onChange={set('Merchant_Category')} options={MERCHANTS} />
              <Select label="Channel" value={form.Transaction_Type} onChange={set('Transaction_Type')} options={CHANNELS} />
              <Select label="Card present" value={form.Card_Present} onChange={set('Card_Present')} options={YES_NO} />
              <Select label="Country matches card" value={form.Country_Match} onChange={set('Country_Match')} options={YES_NO} />
              <Input label="Transaction time (seconds)" type="number" inputMode="numeric" min="0" step="1" value={form.Time} onChange={set('Time')} error={errors.Time} hint="On the dataset clock, 0 to 7,776,000" />
              <Input label="V3 · history signal" type="number" step="0.1" value={form.V3} onChange={set('V3')} error={errors.V3} hint="Higher in fraud" />
              <Input label="V14 · location variance" type="number" step="0.1" value={form.V14} onChange={set('V14')} error={errors.V14} hint="Lower in fraud" />
              <Input label="V17 · spending pattern" type="number" step="0.1" value={form.V17} onChange={set('V17')} error={errors.V17} hint="Higher in fraud" />
            </div>
            <Segmented label="Model" name="verify-mode" value={mode} onChange={setMode} options={MODE_OPTIONS} />
            <p className="small muted">Other anonymised features (V1, V2, V4 and so on) are filled with the dataset average.</p>
            <Button type="submit" size="lg" icon={ScanSearch} loading={state.status === 'loading'} block>
              Run fraud check
            </Button>
          </form>
        </Card>

        <div className="stack sticky-side">
          <Card title="Verdict" hover={false}>
            <AnimatePresence mode="wait">
              {state.status === 'idle' && (
                <EmptyState
                  key="idle"
                  icon={ShieldCheck}
                  title="No check run yet"
                  message="Fill in the details or pick an example, then run the check."
                  action={<Button variant="secondary" onClick={() => { applyPreset('legit'); }}>Load a legitimate example</Button>}
                  compact
                />
              )}
              {state.status === 'loading' && (
                <div key="loading" className="stack" role="status" aria-label="Scoring transaction">
                  <Skeleton height={60} radius={20} />
                  <Skeleton height={16} radius={999} />
                  <Skeleton height={90} radius={18} />
                </div>
              )}
              {state.status === 'error' && <ErrorState key="error" title="The check failed" error={state.error} onRetry={submit} compact />}
              {state.status === 'done' && <Result key="done" res={state.res} mode={state.mode} />}
            </AnimatePresence>
          </Card>
          <Card title="Risk bands" hover={false}>
            <div className="bands">
              <div className="band low"><b>Below 40%</b><span>Low risk. Approve instantly.</span></div>
              <div className="band mid"><b>40% to 70%</b><span>Medium. Challenge with 3-D Secure.</span></div>
              <div className="band high"><b>Above 70%</b><span>High. Decline and alert.</span></div>
            </div>
            <p className="small muted" style={{ marginTop: 12 }}>
              <CheckCircle2 size={14} aria-hidden="true" style={{ verticalAlign: -2 }} /> Fraud tends to show a large amount, no card present, an online channel and a country mismatch.
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}

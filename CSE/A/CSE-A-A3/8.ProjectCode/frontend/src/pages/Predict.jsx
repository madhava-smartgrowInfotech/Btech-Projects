import { useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Activity, CheckCircle2, ShieldAlert, ShieldCheck, Sparkles, Stethoscope, Trash2 } from 'lucide-react'
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  ErrorState,
  Input,
  KeyValueList,
  PageHeader,
  ProgressBar,
  Select,
  Skeleton,
  Tabs,
  useToast,
} from '../components/ui'
import { FadeIn } from '../components/motion'
import { api } from '../lib/api'
import { ICON, KEYS } from '../lib/diseases'
import { DISEASE_NAME, pct } from '../lib/format'
import { useAsync } from '../lib/useAsync'

const fmt = (n) => (Number.isInteger(n) ? String(n) : String(Number(n.toFixed(2))))

function validate(fields, values) {
  const errors = {}
  for (const f of fields) {
    const raw = String(values[f.name] ?? '').trim()
    if (raw === '') errors[f.name] = 'Required.'
    else if (!Number.isFinite(Number(raw))) errors[f.name] = 'Enter a number.'
  }
  return errors
}

function Result({ data, resultRef }) {
  const high = data.positive
  const Icon = high ? ShieldAlert : ShieldCheck
  return (
    <div className="result" aria-live="polite">
      <div className="result-verdict">
        <span className={`result-icon ${high ? 'danger' : 'safe'}`}>
          <Icon size={26} aria-hidden="true" />
        </span>
        <div>
          <div className="faint">Prediction</div>
          <h3 className="result-title" ref={resultRef} tabIndex={-1}>
            {data.result}
          </h3>
        </div>
      </div>
      <ProgressBar
        value={data.probability ?? 0}
        max={100}
        label="Model confidence"
        valueLabel={data.probability === null ? 'n/a' : `${data.probability.toFixed(2)}%`}
      />
      <KeyValueList
        items={[
          ['Condition', data.title.replace(' Risk Prediction', '')],
          ['Risk class', <Badge key="r" tone={high ? 'danger' : 'safe'} dot>{high ? 'High risk' : 'Low risk'}</Badge>],
          ['Model used', data.model],
          ['Model test accuracy', pct(data.accuracy)],
        ]}
      />
      <p className="faint">
        Machine-learning estimate for education and demonstration only. It is not a medical diagnosis; consult a qualified healthcare provider.
      </p>
    </div>
  )
}

function PredictForm({ info }) {
  const toast = useToast()
  const resultRef = useRef(null)
  const [values, setValues] = useState({})
  const [errors, setErrors] = useState({})
  const [run, setRun] = useState({ status: 'idle', data: null, error: null })
  const [sampling, setSampling] = useState(null)

  const set = (name, v) => {
    setValues((s) => ({ ...s, [name]: v }))
    setErrors((e) => (e[name] ? { ...e, [name]: undefined } : e))
  }

  const submit = async (e) => {
    e?.preventDefault()
    const errs = validate(info.fields, values)
    setErrors(errs)
    if (Object.keys(errs).length) {
      document.getElementById(`f-${info.fields.find((f) => errs[f.name]).name}`)?.focus()
      return
    }
    setRun({ status: 'loading', data: null, error: null })
    try {
      const payload = Object.fromEntries(info.fields.map((f) => [f.name, Number(values[f.name])]))
      const data = await api.predict(info.key, payload)
      setRun({ status: 'done', data, error: null })
      toast({ tone: 'success', title: data.result, message: `${info.title.replace(' Risk Prediction', '')} · confidence ${data.probability?.toFixed(1)}%` })
      requestAnimationFrame(() => {
        resultRef.current?.focus({ preventScroll: true })
        resultRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
      })
    } catch (error) {
      setRun({ status: 'error', data: null, error })
    }
  }

  const loadSample = async (outcome) => {
    setSampling(outcome)
    try {
      const s = await api.sample(info.key, outcome)
      setValues(Object.fromEntries(Object.entries(s.values).map(([k, v]) => [k, fmt(v)])))
      setErrors({})
      setRun({ status: 'idle', data: null, error: null })
      toast({ tone: 'info', title: 'Sample loaded', message: `A real record from the ${info.key} training data, labelled ${s.label === 1 ? 'positive (1)' : 'negative (0)'}. The model may still disagree with that label.` })
    } catch (error) {
      toast({ tone: 'error', title: 'Could not load a sample', message: error.message })
    } finally {
      setSampling(null)
    }
  }

  const clear = () => {
    setValues({})
    setErrors({})
    setRun({ status: 'idle', data: null, error: null })
  }

  return (
    <div className="split">
      <Card>
        <CardHeader
          title="Patient values"
          subtitle={`${info.fields.length} clinical inputs · all required`}
          actions={
            <>
              <Button size="sm" icon={Sparkles} loading={sampling === 1} disabled={sampling !== null} onClick={() => loadSample(1)}>
                Positive sample
              </Button>
              <Button size="sm" icon={Sparkles} loading={sampling === 0} disabled={sampling !== null} onClick={() => loadSample(0)}>
                Negative sample
              </Button>
            </>
          }
        />
        <form className="card-body" onSubmit={submit} noValidate>
          <div className="fields-grid">
            {info.fields.map((f) => {
              const raw = values[f.name] ?? ''
              const out = raw !== '' && Number.isFinite(Number(raw)) && (Number(raw) < f.min || Number(raw) > f.max)
              const common = { id: `f-${f.name}`, label: f.label, error: errors[f.name], value: raw }
              return f.options ? (
                <Select
                  key={f.name}
                  {...common}
                  required
                  onChange={(e) => set(f.name, e.target.value)}
                  options={[{ value: '', label: 'Select…' }, ...f.options.map((o) => ({ value: String(o.value), label: o.label }))]}
                />
              ) : (
                <Input
                  key={f.name}
                  {...common}
                  required
                  type="number"
                  inputMode="decimal"
                  step="any"
                  placeholder={f.placeholder}
                  hint={out ? `Outside the training range (${fmt(f.min)}–${fmt(f.max)}); the estimate may be less reliable.` : `${f.placeholder} · training range ${fmt(f.min)}–${fmt(f.max)}`}
                  onChange={(e) => set(f.name, e.target.value)}
                />
              )
            })}
          </div>
          <div className="form-actions">
            <Button type="submit" variant="primary" size="lg" icon={Activity} loading={run.status === 'loading'}>
              Predict risk
            </Button>
            <Button icon={Trash2} onClick={clear} disabled={run.status === 'loading'}>
              Clear
            </Button>
          </div>
        </form>
      </Card>

      <div className="sticky-col">
        <Card>
          <CardHeader
            title="Result"
            subtitle={`${info.best_model} · ${pct(info.accuracy)} test accuracy`}
            actions={
              <Badge tone="info">Best by F1 {info.f1.toFixed(3)}</Badge>
            }
          />
          <div className="card-body">
            {run.status === 'idle' && (
              <EmptyState icon={Stethoscope} title="No prediction yet">
                Fill in the values, or start from a real record in the training data, then press Predict risk.
              </EmptyState>
            )}
            {run.status === 'loading' && (
              <div aria-busy="true" aria-label="Running prediction" className="result">
                <Skeleton height={52} width="70%" />
                <Skeleton height={10} />
                <Skeleton height={96} />
              </div>
            )}
            {run.status === 'error' && <ErrorState title="Prediction failed" error={run.error} onRetry={submit} />}
            {run.status === 'done' && (
              <FadeIn>
                <Result data={run.data} resultRef={resultRef} />
              </FadeIn>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

export default function Predict() {
  const { disease } = useParams()
  const navigate = useNavigate()
  const valid = KEYS.includes(disease)
  const { data, error, loading, reload } = useAsync(() => api.disease(disease), [disease], { enabled: valid })
  const Icon = ICON[disease] || Stethoscope

  return (
    <div className="container">
      <PageHeader
        crumbs={[{ label: 'Overview', to: '/app' }, { label: 'Predict risk' }, { label: DISEASE_NAME[disease] || 'Unknown' }]}
        title={data?.title || (valid ? `${DISEASE_NAME[disease]} risk prediction` : 'Unknown condition')}
        description={data?.blurb ? `Enter the patient's values. Indicators: ${data.blurb}` : undefined}
        actions={valid && <Icon size={28} aria-hidden="true" style={{ color: 'var(--accent)' }} />}
      />
      {valid && (
        <div style={{ marginBottom: 18, overflowX: 'auto' }}>
          <Tabs
            label="Condition"
            value={disease}
            onChange={(v) => navigate(`/app/predict/${v}`)}
            tabs={KEYS.map((k) => ({ value: k, label: DISEASE_NAME[k], icon: ICON[k] }))}
          />
        </div>
      )}
      {!valid ? (
        <EmptyState icon={CheckCircle2} title="That condition does not exist" actions={<Button as={Link} to="/app/predict/diabetes" variant="primary">Open diabetes prediction</Button>}>
          Choose Diabetes, Heart, Liver or Kidney.
        </EmptyState>
      ) : loading ? (
        <div className="split" aria-busy="true" aria-label="Loading form">
          <Card pad spotlight={false}>
            <div className="fields-grid">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} height={44} />
              ))}
            </div>
          </Card>
          <Card pad spotlight={false}>
            <Skeleton height={160} />
          </Card>
        </div>
      ) : error ? (
        <ErrorState title="Could not load this form" error={error} onRetry={reload} />
      ) : (
        <PredictForm key={disease} info={data} />
      )}
    </div>
  )
}

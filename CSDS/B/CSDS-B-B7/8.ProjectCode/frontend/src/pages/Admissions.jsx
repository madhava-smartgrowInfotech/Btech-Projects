import { useCallback, useState } from 'react'
import { CheckCircle2, FlaskConical, Stethoscope, UserPlus, Wand2 } from 'lucide-react'
import api, { errorMessage } from '../api'
import useFetch from '../lib/useFetch'
import { pct } from '../lib/hospi'
import { useToast } from '../components/ui/Toast'
import { PageHeader } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Checkbox, Input, Select } from '../components/ui/Form'
import { Badge, Card, KeyValueList } from '../components/ui/Display'
import { Alert, EmptyState, ErrorState, SkeletonBlock } from '../components/ui/Feedback'
import { Table } from '../components/ui/Table'

const FACILITY_OPTS = ['A', 'B', 'C', 'D', 'E'].map((f) => ({ value: f, label: `Facility ${f}` }))
const WARD_OPTS = ['General', 'Surgical', 'Maternity', 'Paediatric', 'ICU'].map((w) => ({ value: w, label: w }))
const READMIT_OPTS = [0, 1, 2, 3, 4, 5].map((n) => ({ value: n, label: n === 5 ? '5 or more' : String(n) }))

const CONDITIONS = [
  ['dialysisrenalendstage', 'End-stage renal disease'],
  ['asthma', 'Asthma'],
  ['irondef', 'Iron deficiency'],
  ['pneum', 'Pneumonia'],
  ['substancedependence', 'Substance dependence'],
  ['psychologicaldisordermajor', 'Major psychological disorder'],
  ['depress', 'Depression'],
  ['psychother', 'Other psychological disorder'],
  ['fibrosisandother', 'Fibrosis'],
  ['malnutrition', 'Malnutrition'],
  ['hemo', 'Blood disorder'],
]
const MEASURES = [
  ['hematocrit', 'Hematocrit (g/dL)', 0.1],
  ['neutrophils', 'Neutrophils (cells/µL)', 0.1],
  ['sodium', 'Sodium (mmol/L)', 0.1],
  ['glucose', 'Glucose (mg/dL)', 0.1],
  ['bloodureanitro', 'Blood urea nitrogen (mg/dL)', 0.1],
  ['creatinine', 'Creatinine (mg/dL)', 0.01],
  ['bmi', 'BMI', 0.1],
  ['pulse', 'Pulse (bpm)', 1],
  ['respiration', 'Respiration', 0.1],
  ['secondarydiagnosisnonicd9', 'Secondary diagnoses', 1],
]
const EMPTY = {
  patient_ref: '',
  facility: 'A',
  ward: 'General',
  gender: 'F',
  rcount: 0,
  ...Object.fromEntries(CONDITIONS.map(([k]) => [k, 0])),
  hematocrit: 12,
  neutrophils: 9.5,
  sodium: 137.9,
  glucose: 142,
  bloodureanitro: 12,
  creatinine: 1.1,
  bmi: 29.8,
  pulse: 73,
  respiration: 6.5,
  secondarydiagnosisnonicd9: 1,
}

const fmtImpact = (x) => `${x > 0 ? '+' : ''}${x.toFixed(2)} d`

function Reasons({ result }) {
  const max = Math.max(...result.reasons.map((r) => Math.abs(r.impact_days)), 0.1)
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      <p className="small muted">
        Starting from the average stay of {result.baseline_days} days, each factor adds (red) or removes (green) days.
      </p>
      <ul className="reason-list" aria-label="Factors behind the estimate">
        {result.reasons.map((r) => {
          const shown = Number.isInteger(r.value) ? r.value : Number(r.value).toFixed(1)
          return (
            <li key={r.feature} className="reason-row">
              <span className="reason-label">
                {r.label} <span className="muted">= {shown}</span>
              </span>
              <span className="reason-value">{fmtImpact(r.impact_days)}</span>
              <span className="reason-track" aria-hidden="true">
                <span className={`reason-bar ${r.impact_days > 0 ? 'up' : 'down'}`} style={{ width: `${(Math.abs(r.impact_days) / max) * 50}%` }} />
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function Admissions() {
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [sampleNote, setSampleNote] = useState('')
  const [result, setResult] = useState(null)
  const [admitted, setAdmitted] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const list = useFetch('/admissions')

  const set = (k, v) => {
    setForm((f) => ({ ...f, [k]: v }))
    setResult(null)
    setAdmitted(null)
  }

  const loadSample = async (profile) => {
    setBusy(`sample-${profile}`)
    setError('')
    try {
      const { data } = await api.get('/admissions/sample', { params: { profile } })
      setForm(data.sample)
      setSampleNote(data.source)
      setResult(null)
      setAdmitted(null)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const payload = () => ({ ...form, rcount: Number(form.rcount), secondarydiagnosisnonicd9: Number(form.secondarydiagnosisnonicd9) })

  const predict = async () => {
    setBusy('predict')
    setError('')
    try {
      const { data } = await api.post('/admissions/predict', payload())
      setResult(data)
      setAdmitted(null)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const admit = async () => {
    setBusy('admit')
    setError('')
    try {
      const { data } = await api.post('/admissions', payload())
      setResult({ ...data.prediction, disclaimer: data.disclaimer })
      setAdmitted(data)
      toast.success(`${data.patient_ref} admitted. Forecasts now include this patient.`)
      list.reload()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Admission"
        title="Admissions and predictions"
        description="Predict the length of stay at admission and see the factors behind it. Admitted patients join the forecasts."
        actions={
          <>
            <Button icon={Wand2} onClick={() => loadSample('long')} loading={busy === 'sample-long'} disabled={!!busy && busy !== 'sample-long'}>
              Sample long stay
            </Button>
            <Button icon={Wand2} onClick={() => loadSample('short')} loading={busy === 'sample-short'} disabled={!!busy && busy !== 'sample-short'}>
              Sample short stay
            </Button>
          </>
        }
      />

      {error && (
        <div style={{ marginBottom: 20 }}>
          <Alert tone="error">{error}</Alert>
        </div>
      )}

      <div className="grid" style={{ '--gap': '24px', gridTemplateColumns: 'minmax(0, 3fr) minmax(280px, 2fr)' }}>
        <Card id="admission-form" title="Patient" className="admission-form">
          <div className="stack" style={{ '--gap': '24px' }}>
            {sampleNote && (
              <Alert tone="info">
                <FlaskConical size={16} aria-hidden="true" style={{ verticalAlign: '-3px', marginRight: 6 }} />
                Sample data: {sampleNote}
              </Alert>
            )}

            <fieldset className="fieldset">
              <legend>Admission</legend>
              <div className="grid grid-2" style={{ '--gap': '14px' }}>
                <Input label="Patient reference" value={form.patient_ref} onChange={(e) => set('patient_ref', e.target.value)} placeholder="Generated if empty" maxLength={40} />
                <Select label="Facility" options={FACILITY_OPTS} value={form.facility} onChange={(e) => set('facility', e.target.value)} />
                <Select label="Ward" options={WARD_OPTS} value={form.ward} onChange={(e) => set('ward', e.target.value)} />
                <Select
                  label="Sex"
                  value={form.gender}
                  onChange={(e) => set('gender', e.target.value)}
                >
                  <option value="F">Female</option>
                  <option value="M">Male</option>
                </Select>
                <Select label="Readmissions in 180 days" options={READMIT_OPTS} value={form.rcount} onChange={(e) => set('rcount', Number(e.target.value))} />
              </div>
            </fieldset>

            <fieldset className="fieldset">
              <legend>Conditions</legend>
              <div className="grid grid-2" style={{ '--gap': '12px' }}>
                {CONDITIONS.map(([k, label]) => (
                  <Checkbox key={k} label={label} checked={!!form[k]} onChange={(v) => set(k, v ? 1 : 0)} />
                ))}
              </div>
            </fieldset>

            <fieldset className="fieldset">
              <legend>Labs and vitals</legend>
              <div className="grid grid-2" style={{ '--gap': '14px' }}>
                {MEASURES.map(([k, label, step]) => (
                  <Input
                    key={k}
                    label={label}
                    type="number"
                    step={step}
                    value={form[k]}
                    onChange={(e) => set(k, e.target.value === '' ? '' : Number(e.target.value))}
                  />
                ))}
              </div>
            </fieldset>

            <div className="row">
              <Button onClick={predict} loading={busy === 'predict'} disabled={!!busy && busy !== 'predict'} icon={Stethoscope}>
                Predict stay
              </Button>
              <Button variant="primary" onClick={admit} loading={busy === 'admit'} disabled={!!busy && busy !== 'admit'} icon={UserPlus}>
                Admit patient
              </Button>
            </div>
          </div>
        </Card>

        <Card title="Prediction">
          {busy === 'predict' || busy === 'admit' ? (
            <SkeletonBlock rows={5} label="Running the model" />
          ) : !result ? (
            <EmptyState icon={Stethoscope} title="No prediction yet">
              Fill in the form or load a sample, then press Predict stay. Admit patient also records the admission.
            </EmptyState>
          ) : (
            <div className="stack" style={{ '--gap': '18px' }}>
              {admitted && (
                <Alert tone="success">
                  <CheckCircle2 size={16} aria-hidden="true" style={{ verticalAlign: '-3px', marginRight: 6 }} />
                  {admitted.patient_ref} admitted to Facility {admitted.facility} {admitted.ward}.
                </Alert>
              )}
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <div>
                  <div className="big-number">{result.predicted_days}</div>
                  <div className="small muted">days expected</div>
                </div>
                <Badge tone={result.long_stay ? 'closed' : undefined}>{result.long_stay ? 'Long stay' : 'Short stay'}</Badge>
              </div>
              <KeyValueList
                items={[
                  { label: 'Likely range', value: `${result.range_days[0]} to ${result.range_days[1]} days (80%)` },
                  { label: `Long stay (over ${result.long_stay_threshold_days} d)`, value: pct(result.long_stay_probability) },
                  { label: 'Average stay', value: `${result.baseline_days} days` },
                ]}
              />
              <Reasons result={result} />
              <p className="tiny muted">{result.disclaimer}</p>
            </div>
          )}
        </Card>
      </div>

      <Card title="Admitted in HospiSense" style={{ marginTop: 28 }}>
        {list.error && !list.data ? (
          <ErrorState title="Admissions could not load" error={list.error} onRetry={list.reload} />
        ) : !list.data ? (
          <SkeletonBlock rows={3} label="Loading admissions" />
        ) : (
          <Table
            caption="Patients admitted in HospiSense"
            rows={list.data}
            pageSize={8}
            initialSort={{ key: 'admit_date', dir: 'desc' }}
            empty={
              <EmptyState
                icon={UserPlus}
                title="No admissions recorded yet"
                action={
                  <Button href="#admission-form" icon={Stethoscope}>
                    Predict a patient
                  </Button>
                }
              >
                Admit a patient to see them here and in the forecasts.
              </EmptyState>
            }
            columns={[
              { key: 'patient_ref', label: 'Patient' },
              { key: 'admit_date', label: 'Date' },
              { key: 'location', label: 'Facility / ward', render: (a) => `${a.facility} / ${a.ward}`, sortValue: (a) => `${a.facility}${a.ward}` },
              { key: 'predicted_days', label: 'Predicted stay', numeric: true, render: (a) => `${a.predicted_days} d` },
              { key: 'class', label: 'Class', sortable: false, render: (a) => (a.long_stay ? 'Long' : 'Short') },
              {
                key: 'factor',
                label: 'Top factor',
                sortable: false,
                render: (a) => {
                  const top = a.prediction.reasons[0]
                  return top ? `${top.label} (${fmtImpact(top.impact_days)})` : '—'
                },
              },
              { key: 'created_by', label: 'Entered by', sortable: false },
            ]}
          />
        )}
      </Card>
    </>
  )
}

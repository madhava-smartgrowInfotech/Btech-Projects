import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, HeartPulse, ScanText, Sparkles, Stethoscope } from 'lucide-react'
import { Alert, Button, Card, Input, PageHeader, Select, SkeletonBlock, useToast } from '../components/ui'
import { FileDrop } from '../components/ui'
import { SlideUp } from '../components/motion'
import { FindingChips, LabChips } from '../components/athena/bits'
import { api } from '../lib/api'

const EMPTY = { name: '', age: '', heart_rate: '', sbp: '', dbp: '', spo2: '', temp_c: '', resp_rate: '', arrival_mode: 'walk-in' }
const FIELDS = [
  { key: 'age', label: 'Age (years)', min: 0, max: 120, step: 1 },
  { key: 'heart_rate', label: 'Heart rate (bpm)', min: 20, max: 250, step: 1 },
  { key: 'sbp', label: 'Systolic BP (mmHg)', min: 40, max: 300, step: 1 },
  { key: 'dbp', label: 'Diastolic BP (mmHg)', min: 20, max: 200, step: 1 },
  { key: 'spo2', label: 'SpO2 (%)', min: 50, max: 100, step: 1 },
  { key: 'temp_c', label: 'Temperature (°C)', min: 30, max: 44, step: 0.1 },
  { key: 'resp_rate', label: 'Respiratory rate (/min)', min: 4, max: 70, step: 1 },
]

function validate(v) {
  const errs = {}
  for (const f of FIELDS) {
    const raw = v[f.key]
    if (raw === '' || raw === null) errs[f.key] = 'Required'
    else if (Number.isNaN(Number(raw)) || Number(raw) < f.min || Number(raw) > f.max) errs[f.key] = `${f.min} to ${f.max}`
  }
  return errs
}

export default function NewPatient() {
  const nav = useNavigate()
  const toast = useToast()
  const [file, setFile] = useState(null)
  const [report, setReport] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [extractError, setExtractError] = useState('')
  const [vitals, setVitals] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [samples, setSamples] = useState({ loading: true, items: [], error: null })

  useEffect(() => {
    let live = true
    api
      .samples()
      .then((r) => live && setSamples({ loading: false, items: r.items, error: null }))
      .catch((e) => live && setSamples({ loading: false, items: [], error: e }))
    return () => {
      live = false
    }
  }, [])

  const set = (k) => (e) => setVitals((v) => ({ ...v, [k]: e.target.value }))

  const runExtract = async (f) => {
    setExtracting(true)
    setExtractError('')
    setReport(null)
    try {
      const r = await api.extract(f)
      setReport(r)
      const n = r.symptoms.length + r.findings.length + r.history.length + r.labs.length
      toast.success(`Read ${r.pages.length} page${r.pages.length === 1 ? '' : 's'} and found ${n} items in ${r.seconds}s.`)
    } catch (err) {
      setExtractError(err.message)
    } finally {
      setExtracting(false)
    }
  }

  const onFile = (f) => {
    setFile(f)
    setReport(null)
    setExtractError('')
    if (f) runExtract(f)
  }

  const useSample = async (filename) => {
    if (!filename) return
    const item = samples.items.find((s) => s.filename === filename)
    try {
      const f = await api.sampleFile(filename)
      setVitals({ ...EMPTY, ...Object.fromEntries(Object.entries(item.vitals).map(([k, v]) => [k, String(v)])), name: '' })
      setErrors({})
      onFile(f)
    } catch (err) {
      toast.error(`Could not load the sample: ${err.message}`)
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    const errs = validate(vitals)
    setErrors(errs)
    if (Object.keys(errs).length) {
      toast.warning('Fix the highlighted vitals first.')
      return
    }
    setSaving(true)
    setSaveError('')
    try {
      const body = {
        name: vitals.name,
        vitals: {
          age: Number(vitals.age), heart_rate: Number(vitals.heart_rate), sbp: Number(vitals.sbp), dbp: Number(vitals.dbp),
          spo2: Number(vitals.spo2), temp_c: Number(vitals.temp_c), resp_rate: Number(vitals.resp_rate), arrival_mode: vitals.arrival_mode,
        },
        report,
        ocr_seconds: report?.seconds || 0,
      }
      const p = await api.createPatient(body)
      toast.success(`Priority ${p.priority} assigned (${p.priority_name}).`)
      nav(`/app/patients/${p.id}`)
    } catch (err) {
      setSaveError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Intake"
        title="New patient"
        description="Upload the scanned report, enter the vitals, and ATHENA fuses both into one record before assigning a priority."
      />
      <form onSubmit={submit} noValidate>
        <div className="new-grid">
          <SlideUp>
            <Card title="1 · Scanned report" actions={<FileText size={20} aria-hidden="true" />}>
              <div className="stack">
                {samples.loading ? (
                  <SkeletonBlock rows={1} label="Loading sample reports" />
                ) : samples.items.length > 0 ? (
                  <Select label="Or try a sample report" hint="Generated sample data. Fills the vitals too." value="" onChange={(e) => useSample(e.target.value)}>
                    <option value="">Choose a sample…</option>
                    {samples.items.map((s) => (
                      <option key={s.filename} value={s.filename}>
                        {s.filename.replace(/\.(pdf|png)$/, '').replace(/_/g, ' ')} ({s.kind})
                      </option>
                    ))}
                  </Select>
                ) : null}
                <FileDrop
                  label="Drop the scanned report here"
                  hint="PDF, PNG or JPG · up to 15 MB · or click to browse"
                  accept="application/pdf,image/png,image/jpeg"
                  file={file}
                  onFile={onFile}
                />
                {extracting && (
                  <div aria-live="polite">
                    <p className="small mono">
                      <ScanText size={14} style={{ display: 'inline', verticalAlign: '-2px' }} aria-hidden="true" /> Reading pages… scans take a few seconds.
                    </p>
                    <SkeletonBlock rows={3} label="Reading the report" />
                  </div>
                )}
                {extractError && (
                  <Alert tone="error" action={file && <Button size="sm" onClick={() => runExtract(file)}>Retry</Button>}>
                    {extractError}
                  </Alert>
                )}
                {report && (
                  <div className="stack" aria-live="polite">
                    <Alert tone="success">
                      Read {report.pages.length} page{report.pages.length === 1 ? '' : 's'} ({report.pages.map((p) => p.method).join(', ')}) in {report.seconds}s.
                    </Alert>
                    <div>
                      <h3 className="display-sm" style={{ marginBottom: 8 }}>Symptoms</h3>
                      <FindingChips items={report.symptoms} />
                    </div>
                    <div>
                      <h3 className="display-sm" style={{ marginBottom: 8 }}>Findings</h3>
                      <FindingChips items={report.findings} />
                    </div>
                    <div>
                      <h3 className="display-sm" style={{ marginBottom: 8 }}>History</h3>
                      <FindingChips items={report.history} />
                    </div>
                    <div>
                      <h3 className="display-sm" style={{ marginBottom: 8 }}>Lab values</h3>
                      <LabChips labs={report.labs} />
                    </div>
                  </div>
                )}
                {!file && !extracting && <p className="small muted">No report? You can still triage on vitals alone, but findings from the report will be missing.</p>}
              </div>
            </Card>
          </SlideUp>

          <SlideUp delay={0.08}>
            <Card title="2 · Vitals" actions={<HeartPulse size={20} aria-hidden="true" />}>
              <div className="stack">
                <Input label="Patient label (optional)" placeholder="e.g. Bay 3, walk-in" maxLength={60} value={vitals.name} onChange={set('name')} />
                <div className="vitals-grid">
                  {FIELDS.map((f) => (
                    <Input
                      key={f.key}
                      label={f.label}
                      type="number"
                      inputMode="decimal"
                      min={f.min}
                      max={f.max}
                      step={f.step}
                      value={vitals[f.key]}
                      onChange={set(f.key)}
                      error={errors[f.key]}
                    />
                  ))}
                  <Select
                    label="Arrival mode"
                    value={vitals.arrival_mode}
                    onChange={set('arrival_mode')}
                    options={[
                      { value: 'walk-in', label: 'Walk-in' },
                      { value: 'ambulance', label: 'Ambulance' },
                      { value: 'transfer', label: 'Transfer' },
                    ]}
                  />
                </div>
                {saveError && <Alert tone="error">{saveError}</Alert>}
                <Button variant="primary" size="lg" type="submit" icon={Stethoscope} loading={saving} disabled={extracting} block>
                  {saving ? 'Assigning priority…' : 'Assign priority'}
                </Button>
                <p className="small muted">
                  <Sparkles size={14} style={{ display: 'inline', verticalAlign: '-2px' }} aria-hidden="true" /> Decision support only. The clinician can accept or change the result.
                </p>
              </div>
            </Card>
          </SlideUp>
        </div>
      </form>
    </>
  )
}

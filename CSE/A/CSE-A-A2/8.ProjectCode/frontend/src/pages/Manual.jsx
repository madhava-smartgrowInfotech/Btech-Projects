import { useMemo, useState } from 'react'
import { Download, ScanSearch } from 'lucide-react'
import { Button, Card, Input, PageHeader, useToast } from '../components/ui'
import { PageTransition } from '../components/motion'
import { EventLog } from '../features/EventLog'
import { PipelineError } from '../features/ApiError'
import { ResultPanel } from '../features/ResultPanel'
import { api } from '../lib/api'
import { fmtNum } from '../lib/format'
import { useMonitor } from '../state/MonitorContext'

// min is enforced client-side; the backend itself accepts any float.
const FIELDS = [
  { key: 'acc_x', label: 'Acc X (m/s²)', step: 0.1 },
  { key: 'acc_y', label: 'Acc Y (m/s²)', step: 0.1 },
  { key: 'acc_z', label: 'Acc Z (m/s²)', step: 0.1, hint: '9.81 when the phone is at rest' },
  { key: 'gyro_magnitude', label: 'Gyro magnitude (rad/s)', step: 0.1, min: 0 },
  { key: 'speed_before', label: 'Speed before (km/h)', step: 1, min: 0 },
  { key: 'speed_change', label: 'Speed change (km/h)', step: 1, hint: 'Negative = slowing down' },
  { key: 'jerk', label: 'Jerk', step: 0.1, min: 0 },
]
const DEFAULTS = { acc_x: '0', acc_y: '0', acc_z: '9.81', gyro_magnitude: '0.1', speed_before: '40', speed_change: '0', jerk: '0' }

export default function Manual() {
  const m = useMonitor()
  const toast = useToast()
  const [form, setForm] = useState(DEFAULTS)
  const [errors, setErrors] = useState({})
  const [loadingSample, setLoadingSample] = useState(false)

  const accMag = useMemo(() => {
    const [x, y, z] = ['acc_x', 'acc_y', 'acc_z'].map((k) => parseFloat(form[k]))
    return [x, y, z].every(Number.isFinite) ? Math.sqrt(x * x + y * y + z * z) : null
  }, [form])

  const set = (k) => (e) => {
    setForm((f) => ({ ...f, [k]: e.target.value }))
    setErrors((er) => ({ ...er, [k]: undefined }))
  }

  const validate = () => {
    const er = {}
    for (const f of FIELDS) {
      const raw = form[f.key].trim()
      const v = Number(raw)
      if (raw === '' || !Number.isFinite(v)) er[f.key] = 'Enter a number.'
      else if (f.min !== undefined && v < f.min) er[f.key] = `Must be ${f.min} or more.`
    }
    setErrors(er)
    return Object.keys(er).length === 0
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!validate()) {
      toast.warning('Fix the highlighted fields first.')
      return
    }
    const v = Object.fromEntries(FIELDS.map((f) => [f.key, Number(form[f.key])]))
    // Same payload shape the original dashboard sent: the rotation is carried on gyro_z.
    const reading = { ...v, gyro_x: 0, gyro_y: 0, gyro_z: v.gyro_magnitude, acc_magnitude: Math.sqrt(v.acc_x ** 2 + v.acc_y ** 2 + v.acc_z ** 2) }
    const r = await m.runReading(reading, 'manual')
    if (r) toast.success(`Detection finished: ${r.accident_detected ? `accident, ${r.severity_label}` : 'no accident'}.`)
  }

  const loadSample = async () => {
    setLoadingSample(true)
    try {
      const s = await api.simulate('random')
      const r1 = (n) => String(Math.round(n * 10) / 10)
      setForm({ acc_x: r1(s.acc_x), acc_y: r1(s.acc_y), acc_z: r1(s.acc_z), gyro_magnitude: r1(s.gyro_magnitude), speed_before: String(Math.round(s.speed_before)), speed_change: String(Math.round(s.speed_change)), jerk: r1(s.jerk) })
      setErrors({})
      toast.info(`Loaded a simulated "${s.scenario}" reading. Edit it, then run detection.`)
    } catch (e) {
      toast.error(`Could not load a sample: ${e.message}`)
    } finally {
      setLoadingSample(false)
    }
  }

  return (
    <PageTransition>
      <PageHeader
        eyebrow="Manual override"
        title="Type the sensors"
        description="Enter your own accelerometer, gyroscope and speed values and run the same detection pipeline on them."
      />
      <PipelineError />
      <div className="grid grid-2" style={{ '--gap': '24px', alignItems: 'start' }}>
        <Card title="Sensor values">
          <form onSubmit={submit} noValidate className="stack" aria-describedby="acc-mag">
            <div className="grid grid-2" style={{ '--gap': '16px' }}>
              {FIELDS.map((f) => (
                <Input key={f.key} label={f.label} hint={f.hint} type="number" inputMode="decimal" step={f.step} min={f.min} value={form[f.key]} onChange={set(f.key)} error={errors[f.key]} />
              ))}
            </div>
            <p id="acc-mag" className="small mono muted">
              Derived acc. magnitude: <strong>{accMag === null ? '—' : `${fmtNum(accMag)} m/s²`}</strong>
            </p>
            <div className="row">
              <Button type="submit" variant="primary" icon={ScanSearch} loading={m.busy} disabled={Boolean(m.pending)}>
                Run detection
              </Button>
              <Button icon={Download} loading={loadingSample} onClick={loadSample}>
                Load simulated sample
              </Button>
              <Button variant="ghost" onClick={() => { setForm(DEFAULTS); setErrors({}) }}>
                Reset
              </Button>
            </div>
          </form>
        </Card>
        <div className="stack" style={{ '--gap': '24px' }}>
          <ResultPanel result={m.result} busy={m.busy} />
          <EventLog events={m.events} />
        </div>
      </div>
    </PageTransition>
  )
}

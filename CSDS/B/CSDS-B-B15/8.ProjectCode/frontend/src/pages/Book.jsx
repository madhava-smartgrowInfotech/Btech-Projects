import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertOctagon, Building2, Crosshair, MapPin, Sparkles, Stethoscope, X } from 'lucide-react'
import api, { dateInDays, describeError, todayStr } from '../api'
import { useAuth } from '../auth'
import MapView from '../components/MapView'
import { PageHeader } from '../components/ui/AppShell'
import { Button, IconButton, Input, Select, SearchField, Textarea } from '../components/ui/controls'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import { EmptyState, ErrorState, ProgressBar, Skeleton, useToast } from '../components/ui/feedback'
import { Stepper } from '../components/ui/nav'
import { SEVERITY_TONE, SEVERITY_VAR } from '../format'
import useApi from '../lib/useApi'

const STEPS = [
  { id: 'symptoms', label: 'Symptoms' },
  { id: 'severity', label: 'Severity' },
  { id: 'hospital', label: 'Hospital' },
  { id: 'token', label: 'Token' },
]

// neighbourhoods with coordinates; the browser location is an option too
const LOCALITIES = [
  ['Ameerpet', 17.4375, 78.4483], ['Banjara Hills', 17.4156, 78.4347], ['Begumpet', 17.4447, 78.4664],
  ['Charminar', 17.3616, 78.4747], ['Dilsukhnagar', 17.3687, 78.5247], ['Gachibowli', 17.4401, 78.3489],
  ['Himayatnagar', 17.401, 78.487], ['Kondapur', 17.46, 78.357], ['Kukatpally', 17.4849, 78.4138],
  ['LB Nagar', 17.3457, 78.5522], ['Madhapur', 17.4483, 78.3915], ['Malakpet', 17.373, 78.501],
  ['Mehdipatnam', 17.395, 78.44], ['Secunderabad', 17.4399, 78.4983], ['Uppal', 17.4058, 78.5591],
]
const SEVERITY_HEX = { mild: '#4ade80', moderate: '#fbbf24', severe: '#fb923c', critical: '#f87171' }
const GENDER = [
  ['', 'Not stated'],
  ['F', 'Female'],
  ['M', 'Male'],
]

export default function Book() {
  const { user } = useAuth()
  const nav = useNavigate()
  const toast = useToast()
  const vocab = useApi(() => api.get('/symptoms').then((r) => r.data), [])

  const [step, setStep] = useState('symptoms')
  const [selected, setSelected] = useState([])
  const [query, setQuery] = useState('')
  const [text, setText] = useState('')
  const [mapInfo, setMapInfo] = useState(null)
  const [triage, setTriage] = useState(null)
  const [loc, setLoc] = useState({ name: 'Ameerpet', lat: 17.4375, lon: 78.4483 })
  const [date, setDate] = useState(todayStr())
  const [recs, setRecs] = useState(null)
  const [chosen, setChosen] = useState(null)
  const [patient, setPatient] = useState({ name: user.name, age: user.age ?? '', gender: user.gender ?? '' })
  const [busy, setBusy] = useState('')
  const [error, setError] = useState(null)

  const byKey = useMemo(() => Object.fromEntries((vocab.data || []).map((v) => [v.key, v])), [vocab.data])
  const options = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (vocab.data || [])
      .filter((v) => !selected.includes(v.key) && (!q || v.label.toLowerCase().includes(q)))
      .slice(0, q ? 60 : 48)
  }, [query, vocab.data, selected])
  const picked = chosen && recs ? recs.find((r) => r.id === chosen) : null
  const userPos = useMemo(() => ({ lat: loc.lat, lon: loc.lon }), [loc])

  const resetDownstream = () => {
    setTriage(null)
    setRecs(null)
    setChosen(null)
  }
  const toggle = (k) => {
    setSelected((s) => (s.includes(k) ? s.filter((x) => x !== k) : [...s, k]))
    resetDownstream()
    setStep('symptoms')
  }

  // runs one backend call; failures show an error box with a retry that runs the same call again
  const run = async (label, fn) => {
    setBusy(label)
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError({ ...describeError(e), retry: () => run(label, fn) })
    } finally {
      setBusy('')
    }
  }

  const mapText = () =>
    run('map', async () => {
      const { data } = await api.post('/triage/map-text', { text })
      setMapInfo(data)
      if (!data.symptoms.length) {
        setError({ message: 'No known symptoms recognised', hint: 'Try describing it another way, or pick symptoms from the list.' })
        return
      }
      setSelected((s) => [...new Set([...s, ...data.symptoms])])
      resetDownstream()
    })

  const checkSeverity = () =>
    run('triage', async () => {
      const { data } = await api.post('/triage', { symptoms: selected })
      setTriage(data)
      setRecs(null)
      setStep('severity')
    })

  const findHospitals = () =>
    run('recommend', async () => {
      const { data } = await api.post('/recommend', {
        lat: loc.lat,
        lon: loc.lon,
        severity: triage.severity,
        specialty: triage.specialty,
        date,
        limit: 3,
      })
      setRecs(data)
      setChosen(data[0]?.id ?? null)
      setStep('hospital')
    })

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setError({ message: 'Location is not available in this browser', hint: 'Pick an area from the list instead.' })
      return
    }
    setBusy('geo')
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setLoc({ name: 'My location', lat: p.coords.latitude, lon: p.coords.longitude })
        setRecs(null)
        setBusy('')
      },
      (e) => {
        setError({ message: `Could not get your location (${e.message})`, hint: 'Pick an area from the list instead.' })
        setBusy('')
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  const book = () =>
    run('book', async () => {
      const { data } = await api.post('/bookings', {
        hospital_id: chosen,
        date,
        symptoms: selected,
        patient_name: patient.name.trim(),
        age: patient.age === '' ? null : Number(patient.age),
        gender: patient.gender || null,
      })
      toast({ tone: 'ok', title: `Token ${data.token} booked`, body: data.allocation })
      nav(`/tokens/${data.id}`, { state: { justBooked: data } })
    })

  const markers = useMemo(
    () =>
      (recs || []).map((r, i) => ({
        id: r.id,
        lat: r.lat,
        lon: r.lon,
        label: `${i + 1}. ${r.name}`,
        permanentLabel: true,
        color: r.id === chosen ? SEVERITY_HEX[triage?.severity] || '#4ade80' : '#7dd3fc',
        radius: r.id === chosen ? 12 : 9,
      })),
    [recs, chosen, triage],
  )

  const areaOptions = [...(loc.name === 'My location' ? [['My location', 'My location']] : []), ...LOCALITIES.map(([n]) => [n, n])]

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow="patient - OP booking"
        title="Book a visit"
        subtitle="Describe your symptoms, check how urgent they are, then pick a hospital and get a token."
      />
      <div className="mb-6">
        <Stepper steps={STEPS} current={step} />
      </div>
      {error && <div className="mb-5"><ErrorState error={error} onRetry={error.retry} /></div>}

      {step === 'symptoms' && (
        <Card title="1 - Your symptoms" eyebrow="describe or pick from the list">
          <div className="space-y-6">
            <div>
              <Textarea
                label="Describe in your own words"
                rows={2}
                placeholder="e.g. fever, cough, breathlessness since two days"
                value={text}
                onChange={(e) => setText(e.target.value)}
                hint={
                  mapInfo
                    ? `Matched ${mapInfo.symptoms.length} symptom(s) using ${mapInfo.source === 'gemini' ? 'Gemini' : 'keyword matching'}.`
                    : 'Read by Gemini when a key is configured, otherwise by a keyword matcher.'
                }
              />
              <Button variant="secondary" size="sm" icon={Sparkles} className="mt-3" loading={busy === 'map'} disabled={text.trim().length < 2} onClick={mapText}>
                Match my description
              </Button>
            </div>

            <div>
              <SearchField label="Search symptoms" value={query} onChange={setQuery} placeholder="Search, e.g. cough" />
              {vocab.error && <div className="mt-3"><ErrorState error={vocab.error} onRetry={vocab.reload} /></div>}
              {!vocab.data && !vocab.error && <Skeleton className="mt-3 h-20 w-full" />}
              <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Symptoms to choose from">
                {options.map((o) => (
                  <button
                    key={o.key}
                    type="button"
                    onClick={() => toggle(o.key)}
                    className="rounded-[4px] border border-line-strong bg-panel-2 px-2.5 py-1 font-mono text-[11px] text-muted transition-colors hover:border-ok/60 hover:text-ok"
                  >
                    {o.label}
                  </button>
                ))}
              </div>
              {vocab.data && (
                <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.12em] text-dim">
                  {query ? `${options.length} match(es)` : `Type to narrow ${vocab.data.length} symptoms`}
                </p>
              )}
            </div>

            <div>
              <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Selected ({selected.length})</div>
              {selected.length === 0 ? (
                <p className="text-sm text-dim">No symptoms selected yet.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {selected.map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => toggle(k)}
                      aria-label={`Remove ${byKey[k]?.label || k}`}
                      className="inline-flex items-center gap-1.5 rounded-[4px] border border-ok/40 bg-ok/10 px-2.5 py-1 font-mono text-[11px] text-ok"
                    >
                      {byKey[k]?.label || k}
                      <X size={12} aria-hidden="true" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button icon={Stethoscope} loading={busy === 'triage'} disabled={!selected.length} onClick={checkSeverity}>
                Check severity
              </Button>
            </div>
          </div>
        </Card>
      )}

      {step === 'severity' && triage && (
        <div className="space-y-5">
          <Card title="2 - Assessed severity" eyebrow={`suggested department: ${triage.specialty}`}>
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.14em] text-dim">Severity</div>
                <div className="font-mono text-4xl font-semibold capitalize" style={{ color: SEVERITY_VAR[triage.severity] }}>
                  {triage.severity}
                </div>
              </div>
              <Badge tone={SEVERITY_TONE[triage.severity]} dot>
                {triage.condition}
              </Badge>
            </div>
            {triage.emergency && (
              <div role="alert" className="mt-5 flex gap-3 rounded-[6px] border border-alert/50 bg-alert/10 p-3 text-sm text-fg">
                <AlertOctagon className="mt-0.5 h-5 w-5 shrink-0 text-alert" aria-hidden="true" />
                <div>
                  <b>Possible emergency.</b> Call <a href="tel:108" className="font-semibold underline">108</a> or go to the nearest emergency
                  department now. Emergency-capable hospitals below have a reserved emergency-quota slot.
                </div>
              </div>
            )}
            <p className="mt-5 text-sm text-fg">{triage.advice}</p>
            {triage.description && <p className="mt-2 text-xs text-muted">{triage.description}</p>}

            <div className="mt-6">
              <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Possible conditions (for the doctor)</div>
              <div className="space-y-2">
                {triage.conditions.map((c) => (
                  <ProgressBar key={c.condition} label={c.condition} value={Math.round(c.probability * 100)} tone="info" segments={30} />
                ))}
              </div>
            </div>

            <details className="mt-6 text-sm">
              <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Why this severity?</summary>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                {triage.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </details>
            <p className="mt-6 border-l-2 border-line-strong pl-3 text-xs text-muted">{triage.disclaimer}</p>
          </Card>

          <Card title="3 - Where and when" eyebrow="pick an area and a visit date">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="flex items-end gap-2 sm:col-span-2">
                <Select
                  label="Your area"
                  options={areaOptions}
                  value={loc.name}
                  className="min-w-0 flex-1"
                  onChange={(e) => {
                    const l = LOCALITIES.find((x) => x[0] === e.target.value)
                    if (l) setLoc({ name: l[0], lat: l[1], lon: l[2] })
                    setRecs(null)
                  }}
                />
                <IconButton icon={Crosshair} label="Use my location" onClick={useMyLocation} disabled={busy === 'geo'} />
              </div>
              <Input label="Visit date" type="date" min={todayStr()} max={dateInDays(30)} value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div className="mt-5 flex justify-between gap-3">
              <Button variant="secondary" onClick={() => setStep('symptoms')}>
                Back
              </Button>
              <Button icon={MapPin} loading={busy === 'recommend'} onClick={findHospitals}>
                Suggest hospitals
              </Button>
            </div>
          </Card>
        </div>
      )}

      {step === 'hospital' && (
        <div className="space-y-5">
          {busy === 'recommend' && <Skeleton className="h-72 w-full" />}
          {recs && recs.length === 0 && (
            <EmptyState
              icon={Building2}
              title="No matching hospitals"
              body="No hospital in this network has the department for this severity on that date. Try another date or area."
              action={
                <Button variant="secondary" onClick={() => { setDate(dateInDays(1)); setStep('severity') }}>
                  Change date or area
                </Button>
              }
            />
          )}
          {recs && recs.length > 0 && (
            <Card title="4 - Choose a hospital" eyebrow={`${recs.length} ranked by severity, distance, department and free slots`}>
              <MapView markers={markers} user={userPos} height={300} onSelect={setChosen} />
              <div role="radiogroup" aria-label="Hospitals" className="mt-5 grid gap-2">
                {recs.map((r, i) => {
                  const on = chosen === r.id
                  const pct = Math.min(100, (100 * r.booked) / Math.max(r.op_limit, 1))
                  return (
                    <button
                      key={r.id}
                      type="button"
                      role="radio"
                      aria-checked={on}
                      onClick={() => setChosen(r.id)}
                      className="w-full rounded-[6px] border border-line-strong bg-panel-2 p-3 text-left transition-colors hover:border-ok/50"
                      style={on ? { borderColor: 'var(--ok)', background: 'color-mix(in oklab, var(--ok) 8%, var(--panel-2))' } : undefined}
                    >
                      <div className="flex items-start gap-3">
                        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-[4px] border border-line-strong font-mono text-xs text-fg">{i + 1}</span>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium text-fg">{r.name}</span>
                            {r.specialty_match && <Badge tone="ok">dept matched</Badge>}
                            {r.has_emergency && <Badge tone="alert">emergency</Badge>}
                          </div>
                          <div className="mt-0.5 font-mono text-[11px] text-muted">
                            {r.distance_km} km - {r.why.join(' - ')}
                          </div>
                          <div className="mt-2">
                            <ProgressBar value={pct} tone={pct > 85 ? 'alert' : 'ok'} segments={24} />
                          </div>
                          <div className="mt-1 font-mono text-[10px] text-dim">
                            {r.booked}/{r.op_limit} booked on {date} - {r.free_slots} slots free
                          </div>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
              <div className="mt-5 flex justify-between gap-3">
                <Button variant="secondary" onClick={() => setStep('severity')}>
                  Back
                </Button>
                <Button disabled={!chosen} onClick={() => setStep('token')}>
                  Continue
                </Button>
              </div>
            </Card>
          )}
        </div>
      )}

      {step === 'token' && (
        <Card title="5 - Confirm your token" eyebrow="wait estimates update live once you have a token">
          <KeyValueList
            items={[
              ['Hospital', picked?.name || '-'],
              ['Visit date', date],
              ['Severity', <span key="s" className="capitalize">{triage?.severity}</span>],
              ['Department', triage?.specialty || '-'],
              ['Symptoms', selected.map((k) => byKey[k]?.label || k).join(', ') || '-'],
            ]}
          />
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <Input label="Patient name" value={patient.name} onChange={(e) => setPatient({ ...patient, name: e.target.value })} required minLength={2} />
            <Input label="Age" type="number" min="0" max="120" value={patient.age} onChange={(e) => setPatient({ ...patient, age: e.target.value })} />
            <Select label="Gender" options={GENDER} value={patient.gender} onChange={(e) => setPatient({ ...patient, gender: e.target.value })} />
          </div>
          <div className="mt-6 flex flex-wrap justify-between gap-3">
            <Button variant="secondary" onClick={() => setStep('hospital')}>
              Back
            </Button>
            <Button size="lg" loading={busy === 'book'} disabled={!chosen || patient.name.trim().length < 2} onClick={book}>
              Book token
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

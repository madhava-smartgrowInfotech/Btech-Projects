import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertOctagon, Check, Crosshair, MapPin, Search, Sparkles, Stethoscope, X } from 'lucide-react'
import api, { errMsg, todayStr } from '../api'
import { useAuth } from '../auth'
import MapView from '../components/MapView'
import { Disclaimer, ErrorBox, SEVERITY_COLOR, SeverityBadge, Spinner } from '../components/ui'

const LOCALITIES = [
  ['Ameerpet', 17.4375, 78.4483],
  ['Banjara Hills', 17.4156, 78.4347],
  ['Begumpet', 17.4447, 78.4664],
  ['Charminar', 17.3616, 78.4747],
  ['Dilsukhnagar', 17.3687, 78.5247],
  ['Gachibowli', 17.4401, 78.3489],
  ['Himayatnagar', 17.401, 78.487],
  ['Kondapur', 17.46, 78.357],
  ['Kukatpally', 17.4849, 78.4138],
  ['LB Nagar', 17.3457, 78.5522],
  ['Madhapur', 17.4483, 78.3915],
  ['Malakpet', 17.373, 78.501],
  ['Mehdipatnam', 17.395, 78.44],
  ['Secunderabad', 17.4399, 78.4983],
  ['Uppal', 17.4058, 78.5591],
]

export default function Book() {
  const { user } = useAuth()
  const nav = useNavigate()
  const [vocab, setVocab] = useState([])
  const [vocabErr, setVocabErr] = useState('')
  const [selected, setSelected] = useState([])
  const [query, setQuery] = useState('')
  const [text, setText] = useState('')
  const [mapInfo, setMapInfo] = useState(null)
  const [patient, setPatient] = useState({ name: user.name, age: user.age ?? '', gender: user.gender ?? '' })
  const [triage, setTriage] = useState(null)
  const [loc, setLoc] = useState({ name: 'Ameerpet', lat: 17.4375, lon: 78.4483 })
  const [date, setDate] = useState(todayStr())
  const [recs, setRecs] = useState(null)
  const [chosen, setChosen] = useState(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const loadVocab = () => {
    setVocabErr('')
    api
      .get('/symptoms')
      .then((r) => setVocab(r.data))
      .catch((e) => setVocabErr(errMsg(e)))
  }
  useEffect(loadVocab, [])

  const byKey = useMemo(() => Object.fromEntries(vocab.map((v) => [v.key, v])), [vocab])
  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return vocab.filter((v) => v.label.toLowerCase().includes(q) && !selected.includes(v.key)).slice(0, 8)
  }, [query, vocab, selected])

  const resetDownstream = () => {
    setTriage(null)
    setRecs(null)
    setChosen(null)
  }
  const toggle = (k) => {
    setSelected((s) => (s.includes(k) ? s.filter((x) => x !== k) : [...s, k]))
    resetDownstream()
  }

  const run = async (label, fn) => {
    setBusy(label)
    setError('')
    try {
      await fn()
    } catch (e) {
      setError(errMsg(e))
    } finally {
      setBusy('')
    }
  }

  const mapText = () =>
    run('map', async () => {
      const { data } = await api.post('/triage/map-text', { text })
      setMapInfo(data)
      if (!data.symptoms.length) throw new Error('No known symptoms recognised - try picking them from the list')
      setSelected((s) => [...new Set([...s, ...data.symptoms])])
      resetDownstream()
    })

  const checkSeverity = () =>
    run('triage', async () => {
      const { data } = await api.post('/triage', { symptoms: selected })
      setTriage(data)
      setRecs(null)
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
      if (!data.length) throw new Error('No matching hospitals found - try another location')
      setRecs(data)
      setChosen(data[0].id)
    })

  const useMyLocation = () => {
    if (!navigator.geolocation) return setError('Location is not available in this browser')
    setBusy('geo')
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setLoc({ name: 'My location', lat: p.coords.latitude, lon: p.coords.longitude })
        setRecs(null)
        setBusy('')
      },
      (e) => {
        setError(`Could not get your location (${e.message}). Pick an area instead.`)
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
        patient_name: patient.name,
        age: patient.age === '' ? null : Number(patient.age),
        gender: patient.gender || null,
      })
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
        color: r.id === chosen ? SEVERITY_COLOR[triage?.severity] || '#0f766e' : '#0f766e',
        radius: r.id === chosen ? 12 : 9,
      })),
    [recs, chosen, triage],
  )
  const userPos = useMemo(() => ({ lat: loc.lat, lon: loc.lon }), [loc])

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <div className="lg:col-span-2 space-y-4">
        <div className="card p-5 space-y-4">
          <h2 className="font-semibold flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-teal-700" /> 1. Your symptoms
          </h2>
          <div>
            <label className="label">Describe in your own words</label>
            <textarea
              className="input"
              rows={2}
              placeholder="e.g. fever, cough, breathlessness since two days"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button className="btn-outline mt-2 w-full" onClick={mapText} disabled={text.trim().length < 2 || busy === 'map'}>
              <Sparkles className="h-4 w-4" /> {busy === 'map' ? 'Reading your description...' : 'Match my description'}
            </button>
            {mapInfo && (
              <p className="text-xs text-slate-500 mt-1">
                Matched {mapInfo.symptoms.length} symptom(s) using {mapInfo.source === 'gemini' ? 'Gemini' : 'keyword matching'}.
              </p>
            )}
          </div>
          <div className="relative">
            <label className="label">Or pick from the list</label>
            <div className="relative">
              <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
              <input className="input !pl-9" placeholder="Search symptoms" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            {vocabErr && <ErrorBox error={vocabErr} onRetry={loadVocab} />}
            {matches.length > 0 && (
              <div className="absolute z-[1100] mt-1 w-full card max-h-60 overflow-auto">
                {matches.map((m) => (
                  <button
                    key={m.key}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-teal-50"
                    onClick={() => {
                      toggle(m.key)
                      setQuery('')
                    }}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-wrap gap-2 min-h-8">
            {selected.length === 0 && <span className="text-sm text-slate-400">No symptoms selected yet</span>}
            {selected.map((k) => (
              <span key={k} className="inline-flex items-center gap-1 rounded-full bg-teal-50 border border-teal-200 px-2.5 py-1 text-sm text-teal-800">
                {byKey[k]?.label || k}
                <button onClick={() => toggle(k)} aria-label="remove">
                  <X className="h-3.5 w-3.5" />
                </button>
              </span>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="col-span-3 sm:col-span-1">
              <label className="label">Patient</label>
              <input className="input" value={patient.name} onChange={(e) => setPatient({ ...patient, name: e.target.value })} />
            </div>
            <div>
              <label className="label">Age</label>
              <input className="input" type="number" min="0" max="120" value={patient.age} onChange={(e) => setPatient({ ...patient, age: e.target.value })} />
            </div>
            <div>
              <label className="label">Gender</label>
              <select className="input" value={patient.gender} onChange={(e) => setPatient({ ...patient, gender: e.target.value })}>
                <option value="">-</option>
                <option value="F">Female</option>
                <option value="M">Male</option>
              </select>
            </div>
          </div>
          <button className="btn-primary w-full" onClick={checkSeverity} disabled={!selected.length || busy === 'triage'}>
            {busy === 'triage' ? 'Assessing...' : 'Check severity'}
          </button>
        </div>

        {triage && (
          <div className={`card p-5 space-y-3 ${triage.severity === 'critical' ? 'border-red-400 ring-2 ring-red-200' : ''}`}>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-500">Assessed severity</span>
              <SeverityBadge level={triage.severity} large />
            </div>
            {triage.emergency && (
              <div className="rounded-lg bg-red-600 text-white p-3 text-sm flex gap-2">
                <AlertOctagon className="h-5 w-5 shrink-0" />
                <div>
                  <b>Possible emergency.</b> Call <a href="tel:108" className="underline font-bold">108</a> or go to the nearest
                  emergency department now. Emergency-capable hospitals are listed below with a reserved emergency-quota slot.
                </div>
              </div>
            )}
            <p className="text-sm">{triage.advice}</p>
            <div className="text-sm">
              <div className="label">Possible conditions (for the doctor)</div>
              {triage.conditions.map((c) => (
                <div key={c.condition} className="flex items-center gap-2 py-0.5">
                  <div className="w-36 truncate">{c.condition}</div>
                  <div className="flex-1 h-2 rounded bg-slate-100">
                    <div className="h-2 rounded bg-teal-600" style={{ width: `${Math.round(c.probability * 100)}%` }} />
                  </div>
                  <div className="w-10 text-right text-xs text-slate-500">{Math.round(c.probability * 100)}%</div>
                </div>
              ))}
            </div>
            <div className="text-sm">
              <span className="label inline">Suggested department: </span>
              <b>{triage.specialty}</b>
            </div>
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer">Why this severity?</summary>
              <ul className="list-disc ml-4 mt-1">
                {triage.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </details>
            <Disclaimer text={triage.disclaimer} />
          </div>
        )}
      </div>

      <div className="lg:col-span-3 space-y-4">
        <div className={`card p-5 space-y-4 ${!triage ? 'opacity-50 pointer-events-none' : ''}`}>
          <h2 className="font-semibold flex items-center gap-2">
            <MapPin className="h-5 w-5 text-teal-700" /> 2. Where and when
          </h2>
          <div className="grid sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <label className="label">Your area</label>
              <div className="flex gap-2">
                <select
                  className="input"
                  value={loc.name}
                  onChange={(e) => {
                    const l = LOCALITIES.find((x) => x[0] === e.target.value)
                    if (l) setLoc({ name: l[0], lat: l[1], lon: l[2] })
                    setRecs(null)
                  }}
                >
                  {loc.name === 'My location' && <option>My location</option>}
                  {LOCALITIES.map(([n]) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
                <button className="btn-outline !px-3" onClick={useMyLocation} title="Use my location" disabled={busy === 'geo'}>
                  <Crosshair className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div>
              <label className="label">Visit date</label>
              <input className="input" type="date" min={todayStr()} value={date} onChange={(e) => { setDate(e.target.value); setRecs(null) }} />
            </div>
          </div>
          <button className="btn-primary w-full" onClick={findHospitals} disabled={!triage || busy === 'recommend'}>
            {busy === 'recommend' ? 'Finding hospitals...' : 'Suggest hospitals'}
          </button>
        </div>

        <ErrorBox error={error} />
        {busy === 'recommend' && <Spinner label="Ranking hospitals by severity, distance, specialty and availability" />}

        {recs && (
          <div className="card p-5 space-y-4">
            <h2 className="font-semibold">3. Choose a hospital</h2>
            <MapView markers={markers} user={userPos} height={300} onSelect={setChosen} />
            <div className="space-y-2">
              {recs.map((r, i) => (
                <button
                  key={r.id}
                  onClick={() => setChosen(r.id)}
                  className={`w-full text-left rounded-xl border p-3 transition ${
                    chosen === r.id ? 'border-teal-600 bg-teal-50 ring-2 ring-teal-600/20' : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="grid place-items-center h-7 w-7 rounded-full bg-teal-700 text-white text-sm font-bold shrink-0">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium flex items-center gap-2">
                        {r.name} {chosen === r.id && <Check className="h-4 w-4 text-teal-700" />}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">{r.why.join(' - ')}</div>
                      <div className="mt-1 h-1.5 rounded bg-slate-100">
                        <div
                          className={`h-1.5 rounded ${r.booked / r.op_limit > 0.85 ? 'bg-red-500' : 'bg-teal-600'}`}
                          style={{ width: `${Math.min(100, (100 * r.booked) / r.op_limit)}%` }}
                        />
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {r.booked}/{r.op_limit} booked on {date}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <button className="btn-primary w-full !py-3 text-base" onClick={book} disabled={!chosen || busy === 'book'}>
              {busy === 'book' ? 'Booking...' : 'Book token'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

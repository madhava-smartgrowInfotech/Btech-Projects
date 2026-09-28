import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ImagePlus, Loader2, UserPlus } from 'lucide-react'
import api, { errorText } from '../api.js'
import ClinicalForm, { EMPTY_CLINICAL } from '../components/ClinicalForm.jsx'
import { Disclaimer, ErrorBox, Spinner } from '../components/ui.jsx'

export default function NewScreening() {
  const nav = useNavigate()
  const [params] = useSearchParams()
  const [patients, setPatients] = useState(null)
  const [samples, setSamples] = useState([])
  const [loadError, setLoadError] = useState('')
  const [mode, setMode] = useState('existing')
  const [patientId, setPatientId] = useState(params.get('patient') || '')
  const [newPatient, setNewPatient] = useState({ name: '', age: '', sex: 'Male', code: '' })
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [eye, setEye] = useState('Right')
  const [clinical, setClinical] = useState(EMPTY_CLINICAL)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    setLoadError('')
    Promise.all([api.get('/patients'), api.get('/samples')])
      .then(([p, s]) => {
        setPatients(p.data)
        setSamples(s.data)
        if (!p.data.length) setMode('new')
      })
      .catch((e) => setLoadError(errorText(e)))
  }
  useEffect(load, [])

  // Prefill age and sex in the clinical form from the chosen patient
  useEffect(() => {
    const p = mode === 'existing' ? patients?.find((x) => String(x.id) === String(patientId)) : newPatient
    if (p && p.age) setClinical((c) => ({ ...c, age: p.age, sex: p.sex === 'Female' ? 0 : 1 }))
  }, [patientId, mode, patients, newPatient.age, newPatient.sex])

  const pickFile = (f) => {
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  const pickSample = async (s) => {
    setError('')
    try {
      const { data } = await api.get(`/samples/${s.name}`, { responseType: 'blob' })
      pickFile(new File([data], s.name, { type: data.type || 'image/png' }))
    } catch (e) {
      setError(errorText(e))
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!file) return setError('Choose a fundus image first.')
    let sid = null
    try {
      let pid = patientId
      if (mode === 'new') {
        setBusy('Registering patient...')
        const { data } = await api.post('/patients', { ...newPatient, age: Number(newPatient.age), code: newPatient.code || null })
        pid = data.id
      }
      if (!pid) throw new Error('Select a patient.')
      setBusy('Preprocessing, wavelet analysis and retinopathy model...')
      const fd = new FormData()
      fd.append('patient_id', pid)
      fd.append('eye', eye)
      fd.append('file', file)
      const { data: s } = await api.post('/screenings/image', fd)
      sid = s.id
      setBusy('Scoring clinical heart-disease risk...')
      await api.post(`/screenings/${sid}/clinical`, clinical)
      nav(`/screenings/${sid}`)
    } catch (err) {
      if (sid) nav(`/screenings/${sid}`, { state: { clinicalError: errorText(err) } })
      else setError(errorText(err))
    } finally {
      setBusy('')
    }
  }

  if (loadError) return <ErrorBox error={loadError} onRetry={load} />
  if (!patients) return <Spinner />

  return (
    <form onSubmit={submit} className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">New screening</h1>
        <p className="text-sm text-slate-500">Fundus image and clinical parameters for one patient.</p>
      </div>

      <section className="card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold">1. Patient</h2>
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
            {['existing', 'new'].map((m) => (
              <button type="button" key={m} onClick={() => setMode(m)}
                className={`rounded-md px-3 py-1 ${mode === m ? 'bg-white font-medium shadow-sm' : 'text-slate-600'}`}>
                {m === 'existing' ? 'Existing patient' : 'New patient'}
              </button>
            ))}
          </div>
        </div>
        {mode === 'existing' ? (
          <select className="input" required value={patientId} onChange={(e) => setPatientId(e.target.value)}>
            <option value="">Select a patient...</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} - {p.code} ({p.age}, {p.sex})
              </option>
            ))}
          </select>
        ) : (
          <div className="grid gap-3 sm:grid-cols-4">
            <div className="sm:col-span-2">
              <label className="label">Full name</label>
              <input className="input" required value={newPatient.name} onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })} />
            </div>
            <div>
              <label className="label">Age</label>
              <input className="input" type="number" min="1" max="120" required value={newPatient.age}
                onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })} />
            </div>
            <div>
              <label className="label">Sex</label>
              <select className="input" value={newPatient.sex} onChange={(e) => setNewPatient({ ...newPatient, sex: e.target.value })}>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="label">Patient code (optional, generated if empty)</label>
              <input className="input" value={newPatient.code} onChange={(e) => setNewPatient({ ...newPatient, code: e.target.value })} />
            </div>
            <div className="flex items-end text-xs text-slate-500"><UserPlus className="mr-1 h-4 w-4" /> Saved when the screening runs.</div>
          </div>
        )}
      </section>

      <section className="card space-y-4">
        <h2 className="font-semibold">2. Fundus image</h2>
        <div className="grid gap-5 md:grid-cols-[240px_1fr]">
          <label className="flex aspect-square cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500 hover:border-teal-500">
            {preview ? (
              <img src={preview} alt="Selected fundus" className="h-full w-full object-cover" />
            ) : (
              <>
                <ImagePlus className="mb-2 h-8 w-8" /> Click to upload (JPG / PNG)
              </>
            )}
            <input type="file" accept="image/png,image/jpeg" className="hidden" onChange={(e) => pickFile(e.target.files[0])} />
          </label>
          <div className="space-y-4">
            <div className="max-w-xs">
              <label className="label">Eye</label>
              <select className="input" value={eye} onChange={(e) => setEye(e.target.value)}>
                <option>Right</option>
                <option>Left</option>
              </select>
            </div>
            {file && <p className="text-xs text-slate-500">Selected: {file.name} ({(file.size / 1024).toFixed(0)} KB)</p>}
            {samples.length > 0 && (
              <div>
                <p className="label">Or use a labelled sample image (sample data from the held-out test set)</p>
                <div className="grid grid-cols-5 gap-2 sm:grid-cols-8 lg:grid-cols-10">
                  {samples.map((s) => (
                    <button type="button" key={s.name} onClick={() => pickSample(s)} title={`${s.name} - ${s.label ? 'retinopathy' : 'no retinopathy'} (ground truth)`}
                      className={`relative overflow-hidden rounded-md border-2 ${file?.name === s.name ? 'border-teal-600' : 'border-transparent'}`}>
                      <img src={s.url} alt={s.name} loading="lazy" className="aspect-square w-full bg-black object-cover" />
                      <span className={`absolute bottom-0 left-0 right-0 text-[10px] font-medium text-white ${s.label ? 'bg-red-600/80' : 'bg-green-700/80'}`}>
                        {s.label ? 'HR' : 'Normal'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="card space-y-4">
        <h2 className="font-semibold">3. Clinical parameters</h2>
        <ClinicalForm value={clinical} onChange={setClinical} disabled={!!busy} />
      </section>

      <ErrorBox error={error} />
      <div className="flex flex-wrap items-center gap-4">
        <button className="btn-primary px-6 py-2.5" disabled={!!busy}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" />} Run screening
        </button>
        {busy && <span className="text-sm text-slate-500">{busy}</span>}
      </div>
      <Disclaimer />
    </form>
  )
}

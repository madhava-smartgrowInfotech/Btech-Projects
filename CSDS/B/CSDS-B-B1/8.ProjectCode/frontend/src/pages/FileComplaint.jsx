import { Camera, CheckCircle2, Send, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import api, { errorMessage } from '../api.js'
import MapPicker from '../components/MapPicker.jsx'
import { ErrorBox, Spinner } from '../components/ui.jsx'

const EXAMPLES = [
  'हमारे मोहल्ले में पिछले 5 दिन से पानी की सप्लाई बंद है, बच्चे और बुजुर्ग बहुत परेशान हैं।',
  'Main road par bahut bada gaddha hai, kal raat ek bike wala gir gaya. Jaldi theek karwaiye.',
  'Garbage has not been collected from our lane for a week and it is starting to smell.',
]

export default function FileComplaint() {
  const [text, setText] = useState('')
  const [photo, setPhoto] = useState(null)
  const [point, setPoint] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(null)

  function pickPhoto(e) {
    const f = e.target.files?.[0]
    if (!f) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(f.type)) return setError('Photo must be a JPG, PNG or WebP image.')
    if (f.size > 8 * 1024 * 1024) return setError('Photo must be smaller than 8 MB.')
    setError('')
    setPhoto({ file: f, url: URL.createObjectURL(f) })
  }

  async function submit(e) {
    e.preventDefault()
    if (text.trim().length < 15) return setError('Please describe the problem in a little more detail.')
    setBusy(true)
    setError('')
    const fd = new FormData()
    fd.append('text', text)
    if (point) {
      fd.append('lat', point.lat)
      fd.append('lng', point.lng)
    }
    if (photo) fd.append('photo', photo.file)
    try {
      const { data } = await api.post('/complaints', fd)
      setDone(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (done)
    return (
      <div className="mx-auto max-w-lg">
        <div className="card p-8 text-center">
          <CheckCircle2 className="mx-auto h-12 w-12" style={{ color: '#0ca30c' }} />
          <h1 className="mt-4 text-xl font-semibold text-slate-900">Complaint registered</h1>
          <p className="mt-1 text-sm text-slate-600">Keep this tracking ID to follow progress.</p>
          <div className="mt-5 rounded-lg bg-slate-100 py-3 font-mono text-2xl font-semibold tracking-wider text-slate-900">
            {done.tracking_id}
          </div>
          {done.ward && <p className="mt-3 text-sm text-slate-600">Ward: {done.ward}</p>}
          <div className="mt-6 flex justify-center gap-3">
            <Link to={`/track/${done.tracking_id}`} className="btn-primary">
              Track status
            </Link>
            <button
              className="btn-secondary"
              onClick={() => {
                setDone(null)
                setText('')
                setPhoto(null)
                setPoint(null)
              }}
            >
              File another
            </button>
          </div>
        </div>
      </div>
    )

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold text-slate-900">File a complaint</h1>
      <p className="mt-1 text-sm text-slate-600">Write in English, हिंदी or Hinglish. Add a photo and pin the location if you can.</p>
      <form onSubmit={submit} className="card mt-5 space-y-5 p-5">
        <div>
          <label className="label" htmlFor="text">What is the problem?</label>
          <textarea
            id="text"
            className="input min-h-36"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Describe the issue, where it is and since when..."
            maxLength={4000}
          />
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="text-xs text-slate-500">Examples:</span>
            {EXAMPLES.map((ex) => (
              <button key={ex} type="button" onClick={() => setText(ex)} className="max-w-xs truncate rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-600 hover:bg-slate-200">
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="label">Photo (optional)</span>
          {photo ? (
            <div className="relative inline-block">
              <img src={photo.url} alt="Selected" className="h-40 rounded-lg border border-slate-200 object-cover" />
              <button type="button" onClick={() => setPhoto(null)} className="absolute right-1 top-1 rounded-full bg-white p-1 shadow" title="Remove photo">
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-slate-300 px-4 py-6 text-sm text-slate-600 hover:bg-slate-50">
              <Camera className="h-5 w-5 text-slate-500" /> Add a photo (JPG, PNG or WebP, up to 8 MB)
              <input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={pickPhoto} />
            </label>
          )}
        </div>

        <div>
          <span className="label">Location</span>
          <MapPicker value={point} onChange={setPoint} />
        </div>

        <ErrorBox message={error} />
        <div className="flex justify-end">
          <button className="btn-primary" disabled={busy}>
            {busy ? <Spinner /> : <Send className="h-4 w-4" />} {busy ? 'Submitting...' : 'Submit complaint'}
          </button>
        </div>
      </form>
    </div>
  )
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Flag, Loader2, Mic, PackageOpen, Search, Square, Upload } from 'lucide-react'
import api, { currentUser, errorText, fmtDate, fmtTime, label } from '../api.js'
import { Empty, ErrorBox, SampleBadge, ScorePill, SentimentValue, Spinner, StatusBadge } from '../components/ui.jsx'

function Recorder({ agentId, onDone }) {
  const [rec, setRec] = useState(null)
  const [secs, setSecs] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const chunks = useRef([])
  const timer = useRef(null)

  const start = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mr = new MediaRecorder(stream)
      chunks.current = []
      mr.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        clearInterval(timer.current)
        const blob = new Blob(chunks.current, { type: mr.mimeType || 'audio/webm' })
        const ext = (mr.mimeType || '').includes('ogg') ? 'ogg' : 'webm'
        const fd = new FormData()
        fd.append('files', blob, `microphone-${new Date().toISOString().slice(0, 16).replace(':', '')}.${ext}`)
        fd.append('source', 'microphone')
        fd.append('title', `Microphone recording ${new Date().toLocaleString()}`)
        if (agentId) fd.append('agent_id', agentId)
        setBusy(true)
        try {
          await api.post('/calls', fd)
          onDone()
        } catch (err) {
          setError(errorText(err))
        } finally {
          setBusy(false)
          setRec(null)
        }
      }
      mr.start(1000)
      setSecs(0)
      timer.current = setInterval(() => setSecs((s) => s + 1), 1000)
      setRec(mr)
    } catch (err) {
      setError(`Microphone unavailable: ${err.message}`)
    }
  }

  return (
    <div className="space-y-2">
      {!rec ? (
        <button className="btn-secondary w-full" onClick={start} disabled={busy}>
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mic className="h-4 w-4 text-red-600" />}
          {busy ? 'Uploading...' : 'Record from microphone'}
        </button>
      ) : (
        <button className="btn w-full bg-red-600 text-white hover:bg-red-700" onClick={() => rec.stop()}>
          <Square className="h-4 w-4" /> Stop and analyse ({fmtTime(secs)})
        </button>
      )}
      <ErrorBox error={error} />
    </div>
  )
}

export default function Calls() {
  const user = currentUser()
  const sup = user.role === 'supervisor'
  const [calls, setCalls] = useState(null)
  const [agents, setAgents] = useState([])
  const [q, setQ] = useState('')
  const [search, setSearch] = useState('')
  const [agentFilter, setAgentFilter] = useState('')
  const [error, setError] = useState('')
  const [files, setFiles] = useState([])
  const [uploadAgent, setUploadAgent] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [importing, setImporting] = useState(false)
  const [notice, setNotice] = useState('')
  const fileRef = useRef(null)

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/calls', { params: { q: search || undefined, agent_id: agentFilter || undefined } })
      setCalls(data.calls)
      setError('')
    } catch (err) {
      setError(errorText(err))
    }
  }, [search, agentFilter])

  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    api.get('/agents').then((r) => setAgents(r.data)).catch(() => {})
  }, [])
  useEffect(() => {
    if (!calls?.some((c) => c.status === 'queued' || c.status === 'processing')) return
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [calls, load])

  const upload = async () => {
    if (!files.length) return
    setUploading(true)
    setUploadError('')
    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))
    if (uploadAgent) fd.append('agent_id', uploadAgent)
    try {
      const { data } = await api.post('/calls', fd)
      setNotice(`${data.calls.length} recording(s) queued for analysis`)
      setFiles([])
      if (fileRef.current) fileRef.current.value = ''
      load()
    } catch (err) {
      setUploadError(errorText(err))
    } finally {
      setUploading(false)
    }
  }

  const importSamples = async () => {
    setImporting(true)
    setUploadError('')
    try {
      const { data } = await api.post('/studio/import-samples')
      setNotice(data.added ? `${data.added} sample call(s) queued - each takes about a minute to analyse` : 'All sample calls are already loaded')
      load()
    } catch (err) {
      setUploadError(errorText(err))
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
      <div className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Calls</h1>
            <p className="text-sm text-slate-500">{sup ? 'All calls across the team' : 'Your calls'} - search across transcripts</p>
          </div>
          <form
            className="flex flex-wrap gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              setSearch(q.trim())
            }}
          >
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
              <input className="input w-64 pl-8" placeholder="Search transcripts, e.g. refund" value={q} onChange={(e) => setQ(e.target.value)} />
            </div>
            {sup && (
              <select className="input w-40" value={agentFilter} onChange={(e) => setAgentFilter(e.target.value)} aria-label="Filter by agent">
                <option value="">All agents</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            )}
            <button className="btn-secondary">Search</button>
            {search && (
              <button type="button" className="btn-secondary" onClick={() => { setQ(''); setSearch('') }}>Clear</button>
            )}
          </form>
        </div>
        <ErrorBox error={error} onRetry={load} />
        {calls == null ? (
          <Spinner />
        ) : calls.length === 0 ? (
          <Empty>
            {search ? `No calls mention "${search}".` : 'No calls yet. Upload a recording, record one, or generate a sample call in the studio.'}
          </Empty>
        ) : (
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">Call</th>
                  <th className="px-3 py-2">Agent</th>
                  <th className="px-3 py-2">Length</th>
                  <th className="px-3 py-2">Intent</th>
                  <th className="px-3 py-2">Sentiment</th>
                  <th className="px-3 py-2">Score</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {calls.map((c) => (
                  <tr key={c.id} className="border-b border-slate-100 align-top hover:bg-slate-50">
                    <td className="px-4 py-2.5">
                      <Link to={`/calls/${c.id}`} className="font-medium text-indigo-700 hover:underline">
                        {c.title.replace('[Sample] ', '')}
                      </Link>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                        {c.is_sample && <SampleBadge />}
                        {c.source === 'microphone' && <span>microphone</span>}
                        <span>{fmtDate(c.recorded_at)}</span>
                        {c.flags > 0 && (
                          <span className="flex items-center gap-0.5 text-red-600">
                            <Flag className="h-3 w-3" /> {c.flags}
                          </span>
                        )}
                      </div>
                      {c.snippet && <div className="mt-1 max-w-md text-xs italic text-slate-600">{c.snippet}</div>}
                    </td>
                    <td className="px-3 py-2.5">{c.agent || '-'}</td>
                    <td className="px-3 py-2.5">{fmtTime(c.duration)}</td>
                    <td className="px-3 py-2.5 capitalize">{label(c.intent)}</td>
                    <td className="px-3 py-2.5"><SentimentValue value={c.sentiment} /></td>
                    <td className="px-3 py-2.5"><ScorePill score={c.score} /></td>
                    <td className="px-3 py-2.5"><StatusBadge status={c.status} stage={c.stage} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <aside className="space-y-4">
        <div className="card space-y-3">
          <h2 className="h2 mb-0">Add calls</h2>
          <input
            ref={fileRef}
            type="file"
            multiple
            accept="audio/*,.wav,.mp3,.flac,.ogg,.webm,.m4a"
            className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-indigo-50 file:px-3 file:py-1.5 file:text-indigo-800"
            onChange={(e) => setFiles([...e.target.files])}
          />
          {sup && (
            <div>
              <label className="label" htmlFor="ua">Handled by agent</label>
              <select id="ua" className="input" value={uploadAgent} onChange={(e) => setUploadAgent(e.target.value)}>
                <option value="">Unassigned</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
          )}
          <button className="btn-primary w-full" disabled={!files.length || uploading} onClick={upload}>
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload {files.length > 1 ? `${files.length} recordings` : 'recording'}
          </button>
          <Recorder agentId={uploadAgent} onDone={() => { setNotice('Recording queued for analysis'); load() }} />
          <p className="text-xs text-slate-500">
            Stereo recordings are split by channel (agent and customer); single-channel audio uses a turn split.
          </p>
          <ErrorBox error={uploadError} />
          {notice && <div className="rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-800">{notice}</div>}
        </div>
        {sup && (
          <div className="card space-y-2">
            <h2 className="h2 mb-0">Sample data</h2>
            <p className="text-xs text-slate-600">
              Load the 10 bundled sample calls (synthetic voices, clearly labelled) to populate analytics.
            </p>
            <button className="btn-secondary w-full" onClick={importSamples} disabled={importing}>
              {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <PackageOpen className="h-4 w-4" />} Load sample calls
            </button>
          </div>
        )}
      </aside>
    </div>
  )
}

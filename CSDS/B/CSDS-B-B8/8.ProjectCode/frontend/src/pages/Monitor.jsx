import { useEffect, useRef, useState } from 'react'
import { Circle, EyeOff, Loader2, Moon, Play, Square, Video } from 'lucide-react'
import api, { ACTIVITY_COLORS, errMsg, fmtDuration, label, token } from '../api.js'
import Skeleton from '../components/Skeleton.jsx'
import Timeline from '../components/Timeline.jsx'
import { ActivityBadge, ErrorBox, PageTitle } from '../components/ui.jsx'

const CLIP_LABELS = ['walking', 'standing', 'sitting', 'lying', 'drinking', 'picking_up', 'fall']
const FALL_TEXT = {
  normal: ['No fall detected', 'text-green-700 bg-green-50 border-green-200'],
  possible_fall: ['Possible fall - confirming...', 'text-amber-800 bg-amber-50 border-amber-200'],
  confirmed: ['Fall confirmed', 'text-red-700 bg-red-50 border-red-200'],
}

export default function Monitor() {
  const [st, setSt] = useState(null)
  const [settings, setSettings] = useState(null)
  const [source, setSource] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [connErr, setConnErr] = useState('')
  const [segments, setSegments] = useState([])
  const [frameTick, setFrameTick] = useState(0)
  const [clip, setClip] = useState({ label: 'walking', seconds: 5 })
  const [clipMsg, setClipMsg] = useState('')
  const firstLoad = useRef(true)

  useEffect(() => {
    api.get('/settings').then(({ data }) => { setSettings(data); setSource(data.camera_source) })
      .catch((e) => setError(errMsg(e)))
  }, [])

  useEffect(() => {
    let alive = true
    let timer
    const poll = async () => {
      try {
        const { data } = await api.get('/monitor/state')
        if (!alive) return
        setSt(data)
        setConnErr('')
        firstLoad.current = false
      } catch (e) {
        if (alive) setConnErr(errMsg(e))
      }
      if (alive) timer = setTimeout(poll, 150)
    }
    poll()
    return () => { alive = false; clearTimeout(timer) }
  }, [])

  useEffect(() => {
    const load = () => api.get('/reports/daily').then(({ data }) => setSegments(data.timeline)).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  const privacy = settings?.privacy_mode !== false
  useEffect(() => {
    if (privacy || !st?.running) return
    const id = setInterval(() => setFrameTick((t) => t + 1), 200)
    return () => clearInterval(id)
  }, [privacy, st?.running])

  const start = async () => {
    setBusy(true); setError('')
    try { await api.post('/monitor/start', { source }) } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }
  const stop = async () => {
    setBusy(true); setError('')
    try { await api.post('/monitor/stop') } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }
  const togglePrivacy = async () => {
    try {
      const { data } = await api.put('/settings', { privacy_mode: !privacy })
      setSettings(data)
    } catch (e) { setError(errMsg(e)) }
  }
  const record = async () => {
    setClipMsg(''); setError('')
    try {
      await api.post('/monitor/record', clip)
      setClipMsg(`Recording "${label(clip.label)}" keypoints for ${clip.seconds}s...`)
    } catch (e) { setError(errMsg(e)) }
  }

  if (!st && !connErr) return <div className="flex justify-center py-20 text-slate-500"><Loader2 className="animate-spin mr-2" /> Connecting...</div>

  const running = st?.running
  const now = new Date()
  const from = new Date(now.getTime() - 30 * 60 * 1000)
  const live = [...segments]
  if (st?.segment) live.push({ activity: st.segment.activity, start: st.segment.start, end: now.toISOString() })
  const [fallText, fallCls] = running ? FALL_TEXT[st?.fall_state] || FALL_TEXT.normal
    : ['', 'text-slate-600 bg-white border-slate-200']
  const probs = st?.running ? Object.entries(st?.probs || {}).sort((a, b) => b[1] - a[1]) : []

  return (
    <div>
      <PageTitle title="Live monitor" subtitle={settings ? `${settings.room_name} - continuous monitoring` : ''}>
        {running
          ? <button className="btn btn-danger" onClick={stop} disabled={busy}>{busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />} Stop</button>
          : <button className="btn btn-primary" onClick={start} disabled={busy}>{busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Start monitoring</button>}
      </PageTitle>

      <div className="space-y-3 mb-4">
        <ErrorBox error={connErr} />
        <ErrorBox error={error || st?.error} />
      </div>

      {!running && (
        <div className="card p-4 mb-4 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-64">
            <label className="label">Camera source</label>
            <input className="input" value={source} onChange={(e) => setSource(e.target.value)} placeholder="0 or http://192.168.1.20:8080/video" />
            <p className="text-xs text-slate-500 mt-1">0 = this computer's webcam. For a phone, install IP Webcam, tap "Start server" and enter its address followed by /video.</p>
          </div>
          {st?.ended && <p className="text-sm text-slate-600">The video source finished.</p>}
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card p-3">
          <div className="flex flex-wrap items-center gap-2 mb-2 text-xs">
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 ${running ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}`}>
              <Circle className={`w-2 h-2 ${running ? 'fill-green-600 text-green-600' : 'fill-slate-400 text-slate-400'}`} />
              {running ? `Live - ${st.fps} fps` : 'Stopped'}
            </span>
            {running && st.enhanced && <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 bg-indigo-100 text-indigo-800"><Moon className="w-3 h-3" /> Low-light enhancement on</span>}
            {running && <span className="text-slate-500">Brightness {st.brightness}</span>}
            <button onClick={togglePrivacy} className="ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 border border-slate-300 hover:bg-slate-50">
              {privacy ? <><EyeOff className="w-3 h-3" /> Privacy mode: skeleton only</> : <><Video className="w-3 h-3" /> Video view (not stored)</>}
            </button>
          </div>
          {privacy || !running
            ? <Skeleton keypoints={st?.keypoints} width={st?.frame_w || 640} height={st?.frame_h || 480} color={st?.fall_state === 'normal' ? '#2dd4bf' : '#f87171'} />
            : <img alt="Live view" className="w-full rounded-lg bg-slate-900" src={`/api/monitor/frame.jpg?token=${token()}&t=${frameTick}`} onError={(e) => { e.currentTarget.style.opacity = 0.3 }} onLoad={(e) => { e.currentTarget.style.opacity = 1 }} />}
          {running && !st.person && <p className="text-sm text-slate-500 mt-2">Nobody in view.</p>}
        </div>

        <div className="space-y-4">
          <div className="card p-4">
            <div className="text-xs uppercase tracking-wide text-slate-500">Current activity</div>
            <div className="text-3xl font-semibold capitalize mt-1" style={{ color: ACTIVITY_COLORS[st?.activity] || '#334155' }}>
              {st?.activity === 'no_person' ? 'Nobody in view' : label(st?.activity)}
            </div>
            {running && st?.confidence > 0 && <div className="text-sm text-slate-500">{Math.round(st.confidence * 100)}% confidence</div>}
            <div className="mt-3 space-y-1.5">
              {probs.map(([k, v]) => (
                <div key={k} className="flex items-center gap-2 text-xs">
                  <span className="w-20 capitalize text-slate-600">{label(k)}</span>
                  <div className="flex-1 h-2 rounded bg-slate-100"><div className="h-2 rounded" style={{ width: `${v * 100}%`, background: ACTIVITY_COLORS[k] }} /></div>
                  <span className="w-9 text-right tabular-nums text-slate-500">{Math.round(v * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
          <div className={`rounded-xl border p-4 ${fallCls}`}>
            <div className="text-xs uppercase tracking-wide opacity-70">Fall detection</div>
            <div className="text-lg font-semibold mt-1">{running ? fallText : 'Not monitoring'}</div>
            {running && <div className="text-sm opacity-80 mt-1">Still for {fmtDuration(st.inactive_seconds)}</div>}
          </div>
          <div className="card p-4">
            <div className="text-sm font-medium text-slate-800">Record a training clip</div>
            <p className="text-xs text-slate-500 mt-0.5">Saves keypoints only (no video) to improve the model. Record with the person's consent.</p>
            <div className="flex gap-2 mt-3">
              <select className="input" value={clip.label} onChange={(e) => setClip({ ...clip, label: e.target.value })}>
                {CLIP_LABELS.map((l) => <option key={l} value={l}>{label(l)}</option>)}
              </select>
              <input className="input w-20" type="number" min={2} max={30} value={clip.seconds} onChange={(e) => setClip({ ...clip, seconds: Number(e.target.value) })} />
            </div>
            <button className="btn btn-secondary w-full mt-2" onClick={record} disabled={!running || !!st?.recording}>
              {st?.recording ? `Recording ${label(st.recording.label)} - ${Math.ceil(st.recording.left)}s` : 'Record clip'}
            </button>
            {!st?.recording && (st?.last_clip || clipMsg) && <p className="text-xs text-slate-500 mt-2">{st?.last_clip ? `Saved: ${st.last_clip}` : clipMsg}</p>}
          </div>
        </div>
      </div>

      <div className="card p-4 mt-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-medium text-slate-800">Activity timeline - last 30 minutes</div>
          {st?.segment && <ActivityBadge activity={st.segment.activity} />}
        </div>
        <Timeline segments={live} from={from} to={now} />
      </div>
    </div>
  )
}

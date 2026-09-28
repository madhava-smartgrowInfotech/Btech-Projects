import { useEffect, useRef, useState } from 'react'
import { Camera, CheckCircle2, Plane, Play, Radio, Square, XCircle } from 'lucide-react'
import api, { errMsg, wsUrl } from '../api'
import { ErrorBox, KeyInput, Spinner, Stat, fmt } from '../components/ui'

const HEX64 = /^[0-9a-fA-F]{64}$/

function Sender({ sharedKey, setSharedKey }) {
  const [mode, setMode] = useState('sequence')
  const [seqs, setSeqs] = useState([])
  const [cfg, setCfg] = useState({ sequence: '', fps: 12, width: 480 })
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [cam, setCam] = useState(null) // {frames, enc_ms}
  const camRef = useRef({})
  const videoRef = useRef(null)

  useEffect(() => {
    api.get('/live/sequences').then((r) => {
      setSeqs(r.data)
      if (r.data.length) setCfg((c) => ({ ...c, sequence: r.data[0].name }))
    }).catch((e) => setError(errMsg(e)))
    const t = setInterval(() => api.get('/live/status').then((r) => setStatus(r.data)).catch(() => {}), 1000)
    return () => { clearInterval(t); stopCam() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const start = async () => {
    setBusy(true); setError('')
    try { await api.post('/live/start', { ...cfg, key: sharedKey }) } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }
  const stop = async () => {
    try { await api.post('/live/stop') } catch (e) { setError(errMsg(e)) }
  }

  const startCam = async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
      videoRef.current.srcObject = stream
      await videoRef.current.play()
      const ws = new WebSocket(wsUrl('/live/camera'))
      ws.binaryType = 'arraybuffer'
      const canvas = document.createElement('canvas')
      let pending = false
      ws.onopen = () => {
        ws.send(JSON.stringify({ key: sharedKey, width: cfg.width }))
        camRef.current.timer = setInterval(() => {
          if (pending || ws.readyState !== 1) return
          const v = videoRef.current
          canvas.width = v.videoWidth; canvas.height = v.videoHeight
          canvas.getContext('2d').drawImage(v, 0, 0)
          pending = true
          canvas.toBlob((b) => b.arrayBuffer().then((buf) => ws.send(buf)), 'image/jpeg', 0.85)
        }, 1000 / cfg.fps)
      }
      ws.onmessage = (m) => {
        const d = JSON.parse(m.data)
        pending = false
        if (d.error) setError(d.error)
        else setCam(d)
      }
      ws.onerror = () => setError('Camera uplink connection failed')
      camRef.current = { ...camRef.current, ws, stream }
      setCam({ frame: 0 })
    } catch (e) {
      setError(e.name === 'NotAllowedError' ? 'Camera permission was denied' : `Camera unavailable: ${e.message}`)
    }
  }
  const stopCam = () => {
    const c = camRef.current
    clearInterval(c.timer)
    c.ws?.close()
    c.stream?.getTracks().forEach((t) => t.stop())
    camRef.current = {}
    setCam(null)
  }

  const s = status?.sender || {}
  const running = mode === 'sequence' ? s.running : !!cam
  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2"><Plane className="h-5 w-5 text-sky-600" /><h2 className="h2">UAV sender</h2>
        {running && <span className="ml-auto flex items-center gap-1 text-xs font-medium text-emerald-600"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" /> transmitting</span>}
      </div>
      <div className="flex rounded-lg bg-slate-100 p-1 text-sm">
        {[['sequence', 'Drone sequence'], ['camera', 'Webcam']].map(([m, l]) => (
          <button key={m} disabled={running} onClick={() => setMode(m)} className={`flex-1 rounded-md py-1.5 ${mode === m ? 'bg-white font-medium shadow' : 'text-slate-500'}`}>{l}</button>
        ))}
      </div>
      <KeyInput value={sharedKey} onChange={setSharedKey} label="Link key (shared with the ground station)" />
      {mode === 'sequence' && (
        <div>
          <label className="label">Sequence (VisDrone sample)</label>
          <select className="input" value={cfg.sequence} onChange={(e) => setCfg({ ...cfg, sequence: e.target.value })}>
            {seqs.map((q) => <option key={q.name} value={q.name}>{q.name} ({q.frames} frames)</option>)}
          </select>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div><label className="label">Target FPS</label><input type="number" min="1" max="30" className="input" value={cfg.fps} onChange={(e) => setCfg({ ...cfg, fps: Number(e.target.value) })} /></div>
        <div><label className="label">Frame width (px)</label>
          <select className="input" value={cfg.width} onChange={(e) => setCfg({ ...cfg, width: Number(e.target.value) })}>
            {[320, 480, 640].map((w) => <option key={w} value={w}>{w}</option>)}
          </select></div>
      </div>
      {mode === 'sequence' ? (
        <div className="flex gap-2">
          <button className="btn-primary flex-1" onClick={start} disabled={busy || !HEX64.test(sharedKey) || !cfg.sequence}>
            {busy ? <Spinner label="Starting..." /> : <><Play className="h-4 w-4" /> {s.running ? 'Restart' : 'Start transmission'}</>}
          </button>
          <button className="btn-danger" onClick={stop} disabled={!s.running}><Square className="h-4 w-4" /> Stop</button>
        </div>
      ) : (
        <div className="flex gap-2">
          <button className="btn-primary flex-1" onClick={startCam} disabled={!!cam || !HEX64.test(sharedKey)}><Camera className="h-4 w-4" /> Start webcam</button>
          <button className="btn-danger" onClick={stopCam} disabled={!cam}><Square className="h-4 w-4" /> Stop</button>
        </div>
      )}
      <video ref={videoRef} muted playsInline className={`w-full rounded-lg ${mode === 'camera' && cam ? '' : 'hidden'}`} />
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Frames sent" value={mode === 'sequence' ? (s.frames_sent ?? 0) : (cam?.frame ?? 0)} />
        <Stat label="On-board encryption" value={`${fmt(mode === 'sequence' ? s.last_enc_ms : cam?.enc_ms, 1)} ms`} />
        <Stat label="Uplink rate" value={`${fmt(status?.uplink?.fps, 1)} fps`} />
        <Stat label="Uplink throughput" value={`${fmt(status?.uplink?.throughput_mbps, 1)} Mbit/s`} />
      </div>
      {s.error && <ErrorBox error={`Sender stopped: ${s.error}`} />}
      <ErrorBox error={error} />
      <p className="text-xs text-slate-500">Only ciphertext travels over the uplink WebSocket. Each frame is encrypted with a fresh 128-bit nonce.</p>
    </div>
  )
}

function Ground({ sharedKey }) {
  const [key, setKey] = useState('')
  const [state, setState] = useState('idle') // idle | connecting | live
  const [frame, setFrame] = useState(null)
  const [error, setError] = useState('')
  const wsRef = useRef(null)

  useEffect(() => { if (!key && sharedKey) setKey(sharedKey) }, [sharedKey, key])
  useEffect(() => () => wsRef.current?.close(), [])

  const connect = () => {
    setError(''); setState('connecting'); setFrame(null)
    const ws = new WebSocket(wsUrl('/live/ground'))
    ws.onopen = () => ws.send(JSON.stringify({ key }))
    ws.onmessage = (m) => {
      const d = JSON.parse(m.data)
      if (d.error) { setError(d.error); return }
      if (d.ready) { setState('live'); return }
      setFrame(d)
    }
    ws.onclose = () => setState('idle')
    ws.onerror = () => setError('Ground station connection failed - is the backend running?')
    wsRef.current = ws
  }
  const disconnect = () => wsRef.current?.close()

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2"><Radio className="h-5 w-5 text-sky-600" /><h2 className="h2">Ground station</h2>
        {state === 'live' && <span className="ml-auto text-xs font-medium text-emerald-600">receiving</span>}
      </div>
      <KeyInput value={key} onChange={setKey} label="Ground station key" />
      <div className="flex gap-2">
        <button className="btn-primary flex-1" onClick={connect} disabled={state !== 'idle' || !HEX64.test(key)}>
          {state === 'connecting' ? <Spinner label="Connecting..." /> : 'Connect'}
        </button>
        <button className="btn-secondary" onClick={disconnect} disabled={state === 'idle'}>Disconnect</button>
        <button className="btn-secondary" disabled={state !== 'idle' || !HEX64.test(key)} title="Flip one bit of the key"
          onClick={() => setKey((parseInt(key.slice(0, 2), 16) ^ 1).toString(16).padStart(2, '0') + key.slice(2))}>Flip 1 bit</button>
      </div>
      <ErrorBox error={error} />
      {state === 'live' && !frame && <div className="rounded-lg bg-slate-50 p-6 text-center text-sm text-slate-500">Waiting for frames - start the UAV sender.</div>}
      {frame && (
        <>
          <div className={`flex items-center gap-2 rounded-lg p-2 text-sm ${frame.key_match ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
            {frame.key_match ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {frame.key_match ? 'Key matches the sender - frames decrypt correctly' : 'Key does not match the sender - output is noise'}
          </div>
          <img src={frame.plain} alt="decrypted frame" className="w-full rounded-lg border border-slate-200" />
          <div className="grid grid-cols-[1fr_140px] gap-3">
            <div className="grid grid-cols-2 gap-2">
              <Stat label="FPS" value={fmt(frame.fps, 1)} />
              <Stat label="Latency" value={`${fmt(frame.latency_ms, 0)} ms`} sub="capture → decrypted" />
              <Stat label="Throughput" value={`${fmt(frame.throughput_mbps, 1)} Mbit/s`} />
              <Stat label="Enc / dec" value={`${fmt(frame.enc_ms, 0)} / ${fmt(frame.dec_ms, 0)} ms`} />
            </div>
            <div>
              <img src={frame.cipher} alt="cipher frame" className="pixel w-full rounded border border-slate-200" />
              <p className="mt-1 text-xs text-slate-500">What an interceptor sees</p>
              <p className="mt-2 text-xs text-slate-500">Frame #{frame.frame} · {frame.width}×{frame.height}<br />{(frame.bytes / 1024).toFixed(0)} KB · {frame.source}</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default function Live() {
  const [key, setKey] = useState('')
  useEffect(() => { api.get('/keys/new').then((r) => setKey(r.data.key)).catch(() => {}) }, [])
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Live UAV link</h1>
        <p className="text-sm text-slate-500">Connect the ground station, then start the sender. Frames are encrypted on the sender, cross the link as ciphertext and are decrypted at the ground station.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <Sender sharedKey={key} setSharedKey={setKey} />
        <Ground sharedKey={key} />
      </div>
    </div>
  )
}

import { Camera, Play, Radio, Square } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import api, { describeError, wsUrl } from '../api'
import ImagePanel from '../components/product/ImagePanel'
import KeyField, { keyReady } from '../components/product/KeyField'
import ActivityLog from '../components/ui/ActivityLog'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Input, Select } from '../components/ui/controls'
import { Badge, Card, KeyValueList, StatCard, StatusDot } from '../components/ui/display'
import { Tabs, TabPanel } from '../components/ui/nav'
import { EmptyState, ErrorState, useToast } from '../components/ui/feedback'
import { flipBit, num } from '../format'

export default function Live() {
  const [linkKey, setLinkKey] = useState('')

  return (
    <>
      <PageHeader eyebrow="uplink carries ciphertext only"
        title="Live UAV link"
        subtitle="A UAV sender encrypts every frame and streams the ciphertext over a WebSocket. A ground station decrypts with its own copy of the key." />

      <Card title="Link key" eyebrow="shared by the sender and the ground station" className="mb-6">
        <KeyField id="link-key" value={linkKey} onChange={setLinkKey} label="Link key (64 hex characters)" />
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Sender linkKey={linkKey} />
        <Ground linkKey={linkKey} />
      </div>

      <div className="mt-6">
        <ActivityLog height={240} title="live-link.log" />
      </div>
    </>
  )
}

// ---- UAV sender: a bundled drone sequence, or the webcam ----
function Sender({ linkKey }) {
  const [mode, setMode] = useState('sequence')
  return (
    <Card title="UAV sender" eyebrow="encrypt and send" className="min-w-0">
      <Tabs id="sender" label="Sender source" value={mode} onChange={setMode}
        tabs={[{ id: 'sequence', label: 'Sample flight' }, { id: 'camera', label: 'Webcam' }]} />
      <div className="pt-4">
        <TabPanel tabsId="sender" value="sequence">
          {mode === 'sequence' && <SequenceSender linkKey={linkKey} />}
        </TabPanel>
        <TabPanel tabsId="sender" value="camera">
          {mode === 'camera' && <CameraSender linkKey={linkKey} />}
        </TabPanel>
      </div>
    </Card>
  )
}

function SequenceSender({ linkKey }) {
  const toast = useToast()
  const [seqs, setSeqs] = useState(null)
  const [seqError, setSeqError] = useState(null)
  const [sequence, setSequence] = useState('')
  const [fps, setFps] = useState(12)
  const [width, setWidth] = useState(480)
  const [status, setStatus] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/live/sequences')
      .then((r) => { setSeqs(r.data); if (r.data.length) setSequence(r.data[0].name) })
      .catch((e) => setSeqError(describeError(e, 'Could not load flights')))
    const poll = () => api.get('/live/status', { silent: true }).then((r) => setStatus(r.data)).catch(() => {})
    poll()
    const t = setInterval(poll, 1000)
    return () => clearInterval(t)
  }, [])

  const sender = status?.sender || {}
  const running = !!sender.running
  const fpsOk = Number(fps) >= 1 && Number(fps) <= 30
  const widthOk = Number(width) >= 64 && Number(width) <= 1280
  const canStart = !!sequence && keyReady(linkKey) && fpsOk && widthOk && !running && !busy

  async function start() {
    setBusy(true)
    setError(null)
    try {
      await api.post('/live/start', { sequence, key: linkKey, fps: Number(fps), width: Number(width) })
      toast({ tone: 'ok', title: 'Transmission started', body: `${sequence} at ${fps} fps` })
    } catch (e) {
      setError(describeError(e, 'Could not start'))
    } finally {
      setBusy(false)
    }
  }

  async function stop() {
    try {
      await api.post('/live/stop')
      toast({ tone: 'info', title: 'Transmission stopped' })
    } catch (e) {
      setError(describeError(e, 'Could not stop'))
    }
  }

  if (seqError) return <ErrorState error={seqError} />
  if (seqs && seqs.length === 0) return <EmptyState title="No flights found" body="The sample drone sequences are missing. Run scripts/download_data.py." />

  return (
    <div className="space-y-4">
      <Select id="sequence" label="Flight" value={sequence} onChange={(e) => setSequence(e.target.value)}
        options={(seqs || []).map((s) => [s.name, `${s.name} · ${s.frames} frames`])} />
      <div className="grid grid-cols-2 gap-3">
        <Input id="fps" type="number" min={1} max={30} label="Frames per second" value={fps} onChange={(e) => setFps(e.target.value)}
          error={fpsOk ? undefined : 'Use 1 to 30'} />
        <Input id="width" type="number" min={64} max={1280} step={2} label="Width (px)" value={width} onChange={(e) => setWidth(e.target.value)}
          error={widthOk ? undefined : 'Use 64 to 1280'} />
      </div>
      <div className="flex flex-wrap gap-2">
        <Button icon={Play} loading={busy} disabled={!canStart} onClick={start}>Start transmission</Button>
        <Button variant="secondary" icon={Square} disabled={!running} onClick={stop}>Stop</Button>
      </div>
      {!keyReady(linkKey) && <p className="font-mono text-[11px] text-dim">enter a link key above to start</p>}
      {error && <ErrorState error={error} compact />}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Sender" value={running ? 'live' : 'stopped'} tone={running ? 'ok' : 'dim'} live={running} />
        <StatCard label="Frames sent" value={sender.frames_sent ?? 0} />
        <StatCard label="Encrypt, last" value={sender.last_enc_ms != null ? `${num(sender.last_enc_ms, 1)} ms` : '—'} />
        <StatCard label="Bytes/frame" value={sender.bytes_per_frame != null ? `${(sender.bytes_per_frame / 1024).toFixed(1)} KB` : '—'} />
      </div>
      {sender.error && <ErrorState error={{ message: `Sender stopped: ${sender.error}` }} compact />}
    </div>
  )
}

// Webcam frames are JPEG-encoded in the browser and encrypted on the server. One frame in flight at a time.
function CameraSender({ linkKey }) {
  const [fps, setFps] = useState(5)
  const [active, setActive] = useState(false)
  const [frames, setFrames] = useState(0)
  const [encMs, setEncMs] = useState(null)
  const [error, setError] = useState(null)
  const video = useRef(null)
  const run = useRef({})

  function stop() {
    const r = run.current
    clearInterval(r.timer)
    if (r.ws && r.ws.readyState <= 1) r.ws.close()
    r.stream?.getTracks().forEach((t) => t.stop())
    run.current = {}
    setActive(false)
  }
  useEffect(() => stop, []) // eslint-disable-line react-hooks/exhaustive-deps -- stop camera on leave

  async function start() {
    setError(null)
    setFrames(0)
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
    } catch (e) {
      setError({ message: 'Camera not available', hint: e?.name === 'NotAllowedError' ? 'Allow camera access for this site and try again.' : (e?.message || 'Check that a camera is connected.') })
      return
    }
    video.current.srcObject = stream
    await video.current.play().catch(() => {})

    const ws = new WebSocket(wsUrl('/live/camera'))
    ws.binaryType = 'arraybuffer'
    const canvas = document.createElement('canvas')
    const r = { stream, ws, pending: false }
    run.current = r
    ws.onopen = () => {
      ws.send(JSON.stringify({ key: linkKey, width: 480 }))
      r.timer = setInterval(() => {
        const v = video.current
        if (r.pending || ws.readyState !== 1 || !v?.videoWidth) return
        canvas.width = v.videoWidth
        canvas.height = v.videoHeight
        canvas.getContext('2d').drawImage(v, 0, 0)
        r.pending = true
        canvas.toBlob((b) => b && b.arrayBuffer().then((buf) => ws.send(buf)), 'image/jpeg', 0.85)
      }, 1000 / fps)
      setActive(true)
    }
    ws.onmessage = (m) => {
      r.pending = false
      const d = JSON.parse(m.data)
      if (d.error) { setError({ message: d.error }); stop(); return }
      setFrames(d.frame)
      setEncMs(d.enc_ms)
    }
    ws.onerror = () => { setError({ message: 'Camera link failed', hint: 'Is the backend running on port 8210?' }); stop() }
    ws.onclose = () => { if (run.current.ws === ws) stop() }
  }

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-[6px] border border-line bg-panel-2">
        <video ref={video} muted playsInline className="aspect-video w-full object-cover" aria-label="Webcam preview" />
        {!active && <div className="p-6 text-center text-xs text-muted">The preview appears when the camera starts.</div>}
      </div>
      <Input id="cam-fps" type="number" min={1} max={30} label="Frames per second" value={fps}
        onChange={(e) => setFps(Math.min(30, Math.max(1, Number(e.target.value) || 1)))} disabled={active} />
      <div className="flex flex-wrap gap-2">
        {!active
          ? <Button icon={Camera} disabled={!keyReady(linkKey)} onClick={start}>Start camera</Button>
          : <Button variant="secondary" icon={Square} onClick={stop}>Stop camera</Button>}
        {active && <Badge tone="ok" dot>sending</Badge>}
      </div>
      {!keyReady(linkKey) && <p className="font-mono text-[11px] text-dim">enter a link key above to start</p>}
      {error && <ErrorState error={error} compact />}
      <div className="grid grid-cols-2 gap-3">
        <StatCard label="Frames sent" value={frames} />
        <StatCard label="Encrypt, last" value={encMs != null ? `${num(encMs, 1)} ms` : '—'} />
      </div>
    </div>
  )
}

// ---- ground station: receives ciphertext, decrypts with its own key ----
function Ground({ linkKey }) {
  const [groundKey, setGroundKey] = useState('')
  const [state, setState] = useState('idle') // idle | connecting | live | error
  const [frame, setFrame] = useState(null)
  const [error, setError] = useState(null)
  const ws = useRef(null)

  // set the ground key to the link key the first time it becomes valid
  useEffect(() => {
    if (!groundKey && keyReady(linkKey)) setGroundKey(linkKey)
  }, [linkKey, groundKey])

  function disconnect() {
    if (ws.current) {
      const s = ws.current
      ws.current = null
      s.close()
    }
    setState('idle')
  }
  useEffect(() => disconnect, []) // eslint-disable-line react-hooks/exhaustive-deps -- close on leave

  function connect(k) {
    disconnect()
    setError(null)
    setFrame(null)
    setState('connecting')
    const s = new WebSocket(wsUrl('/live/ground'))
    ws.current = s
    s.onopen = () => s.send(JSON.stringify({ key: k }))
    s.onmessage = (m) => {
      const d = JSON.parse(m.data)
      if (d.error) { setError({ message: d.error, hint: 'Use the 64-character key the sender uses.' }); setState('error'); return }
      if (d.ready) { setState('live'); return }
      setFrame(d)
    }
    s.onerror = () => { setError({ message: 'Ground station connection failed', hint: 'Is the backend running on port 8210?' }); setState('error') }
    s.onclose = () => { if (ws.current === s) { ws.current = null; setState((st) => (st === 'error' ? st : 'idle')) } }
  }

  const connectable = keyReady(groundKey)
  const busy = state === 'connecting'
  const matched = frame?.key_match

  return (
    <Card title="Ground station" eyebrow="decrypt with its own key" className="min-w-0">
      <div className="space-y-4">
        <div className="flex items-end gap-2">
          <KeyField id="ground-key" value={groundKey} onChange={setGroundKey} label="Ground station key" allowNew={false} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Button icon={Radio} loading={busy} disabled={!connectable || busy} onClick={() => connect(groundKey)}>
            {state === 'live' ? 'Reconnect' : 'Connect'}
          </Button>
          <Button variant="secondary" disabled={state === 'idle' || busy} onClick={disconnect}>Disconnect</Button>
          <Button variant="secondary" disabled={!connectable || busy}
            onClick={() => { const k = flipBit(groundKey); setGroundKey(k); if (state !== 'idle') connect(k) }}>
            Flip 1 bit
          </Button>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted" role="status">
          <StatusDot tone={state === 'live' ? 'ok' : state === 'error' ? 'alert' : state === 'connecting' ? 'warn' : 'dim'} blink={state === 'live'} />
          {{ idle: 'not connected', connecting: 'connecting', live: 'receiving', error: 'error' }[state]}
          {state === 'live' && matched === false && <Badge tone="alert">key mismatch: frames are noise</Badge>}
        </div>
        {error && <ErrorState error={error} compact />}

        {frame ? (
          <>
            <div className="grid grid-cols-2 gap-3">
              <ImagePanel src={frame.cipher} caption="Received cipher" />
              <ImagePanel src={frame.plain} caption={matched ? 'Decrypted' : 'Decrypted with this key'} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Frames/s" value={num(frame.fps, 1)} />
              <StatCard label="Throughput" value={`${num(frame.throughput_mbps, 2)} Mb/s`} />
              <StatCard label="Latency" value={`${num(frame.latency_ms, 1)} ms`} />
              <StatCard label="Decrypt, last" value={`${num(frame.dec_ms, 1)} ms`} />
            </div>
            <KeyValueList items={[
              ['Frame', `#${frame.frame} · ${frame.width}×${frame.height}`],
              ['Source', frame.source],
              ['Payload', `${(frame.bytes / 1024).toFixed(1)} KB`],
            ]} />
          </>
        ) : (
          state === 'live' && <EmptyState title="Waiting for frames" body="Start a transmission on the sender. Frames appear here as they arrive." />
        )}
      </div>
    </Card>
  )
}

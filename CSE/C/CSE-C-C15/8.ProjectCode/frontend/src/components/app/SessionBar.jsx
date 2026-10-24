import { FlaskConical, Play, Radio, Square } from 'lucide-react'
import { useEffect, useState } from 'react'
import api, { describeError } from '../../api'
import { useLive } from '../../lib/live'
import { Button, Input, Select } from '../ui/controls'
import { Badge, Card, StatusDot } from '../ui/display'
import { ErrorState, Skeleton, useToast } from '../ui/feedback'

const MODE = {
  live: { tone: 'alert', label: 'Live capture' },
  simulation: { tone: 'warn', label: 'Simulation mode' },
  stopped: { tone: 'neutral', label: 'Stopped' },
}

// Start / stop a monitoring session. Simulation is always labelled as simulated, never as live traffic.
export default function SessionBar() {
  const { status, loaded, error, busy, startLive, startSim, stop } = useLive()
  const toast = useToast()
  const [ifaces, setIfaces] = useState(null)
  const [ifaceErr, setIfaceErr] = useState(null)
  const [iface, setIface] = useState('')
  const [win, setWin] = useState('10')
  const [formErr, setFormErr] = useState(null)
  const [sessionErr, setSessionErr] = useState(null)

  useEffect(() => {
    let off = false
    api.get('/interfaces').then((r) => {
      if (off) return
      const list = r.data.interfaces || []
      setIfaces(list)
      const pick = list.find((i) => i.up && i.ips.some((ip) => !ip.includes(':') && !ip.startsWith('169.254'))) || list.find((i) => i.up) || list[0]
      if (pick) setIface(pick.name)
    }).catch((e) => { if (!off) setIfaceErr(describeError(e)) })
    return () => { off = true }
  }, [])

  const mode = status?.mode || 'stopped'
  const running = mode !== 'stopped'
  const m = MODE[mode] || MODE.stopped

  function checkWindow() {
    const n = Number(win)
    if (!Number.isInteger(n) || n < 2 || n > 120) {
      setFormErr('Use a whole number from 2 to 120 seconds.')
      return null
    }
    setFormErr(null)
    return n
  }

  async function onLive() {
    const n = checkWindow()
    if (n === null) return
    setSessionErr(null)
    const r = await startLive(iface, n)
    if (r.ok) {
      // The backend accepts the request first and may fail a moment later (no Npcap, no admin rights): look again.
      await new Promise((res) => setTimeout(res, 2200))
      const s = await api.get('/status', { silent: true }).then((x) => x.data).catch(() => null)
      if (s && !s.monitoring && s.capture_error) {
        setSessionErr({ message: s.capture_error, hint: 'Run as administrator with Npcap installed, or use simulation mode.' })
        toast({ tone: 'alert', title: 'Live capture could not run', body: s.capture_error })
      } else toast({ tone: 'ok', title: 'Live capture started', body: `${iface || 'default interface'} · ${n}s windows` })
    } else { setSessionErr({ message: r.error, hint: `${r.hint} Simulation mode needs no capture permissions.` }); toast({ tone: 'alert', title: 'Live capture did not start', body: r.error }) }
  }
  async function onSim() {
    const n = checkWindow()
    if (n === null) return
    setSessionErr(null)
    const r = await startSim(Math.min(n, 10))
    if (r.ok) toast({ tone: 'warn', title: 'Simulation started', body: 'Synthetic windows run through the real model. No packets are sent.' })
    else { setSessionErr({ message: r.error, hint: r.hint }); toast({ tone: 'alert', title: 'Simulation did not start', body: r.error }) }
  }
  async function onStop() {
    setSessionErr(null)
    const r = await stop()
    if (r.ok) toast({ tone: 'info', title: 'Session stopped' })
    else toast({ tone: 'alert', title: 'Could not stop the session', body: r.error })
  }

  return (
    <Card title="Session control" eyebrow="monitor"
      action={loaded ? <Badge tone={m.tone} dot>{m.label}</Badge> : <Skeleton className="h-5 w-24" />}>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,0.6fr)_auto] lg:items-start">
        {ifaces ? (
          <Select label="Capture interface" value={iface} onChange={(e) => setIface(e.target.value)} disabled={running}
            options={ifaces.length ? ifaces.map((i) => [i.name, `${i.display}${i.up ? '' : ' · down'}`]) : [['', 'No interfaces found']]} />
        ) : ifaceErr ? (
          <div className="self-end"><ErrorState compact error={ifaceErr} title="Interfaces unavailable" /></div>
        ) : <div><div className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">Capture interface</div><Skeleton className="h-10 w-full" /></div>}
        <Input label="Window (s)" type="number" inputMode="numeric" min={2} max={120} value={win} disabled={running}
          onChange={(e) => setWin(e.target.value)} error={formErr} />
        <div className="flex flex-wrap items-end gap-2 lg:pt-[26px]">
          <Button icon={Radio} loading={busy === 'live'} disabled={running || !!busy || !!error} onClick={onLive}>Start live</Button>
          <Button variant="secondary" icon={FlaskConical} loading={busy === 'sim'} disabled={running || !!busy || !!error} onClick={onSim}>Start simulation</Button>
          <Button variant="danger" icon={Square} loading={busy === 'stop'} disabled={!running || !!busy} onClick={onStop}>Stop</Button>
        </div>
      </div>
      {mode === 'simulation' && (
        <p className="mt-3 flex items-start gap-2 rounded-[6px] border border-warn/40 bg-warn/10 p-2.5 text-xs text-warn" role="note">
          <FlaskConical size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
          Simulation mode: synthetic traffic windows are generated in software and scored by the real model. Nothing here is live network traffic.
        </p>
      )}
      {mode === 'live' && (
        <p className="mt-3 flex items-center gap-2 font-mono text-xs text-muted">
          <StatusDot tone="alert" ring /> capturing on {status.interface || 'default'} · {status.window_seconds}s windows
        </p>
      )}
      {!running && !error && loaded && (
        <p className="mt-3 flex items-center gap-2 text-xs text-muted"><Play size={13} className="text-ok" aria-hidden="true" />
          Live capture needs administrator rights and Npcap on Windows. Simulation works anywhere and shows the full pipeline.</p>
      )}
      {(sessionErr || status?.capture_error) && (
        <div className="mt-3"><ErrorState compact title={running ? 'Capture problem' : 'Last capture problem'}
          error={sessionErr || { message: status.capture_error, hint: 'Run as administrator with Npcap installed, or use simulation mode.' }} /></div>
      )}
    </Card>
  )
}

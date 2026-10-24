import { AlertOctagon, Ambulance, Car, ChevronsRight, Clock, Play, RotateCcw, ShieldAlert, Square, Timer, Waypoints } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { logEvent } from '../lib/activity'
import { useLive } from '../lib/live'
import { SlideUp, Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Select, Switch } from '../components/ui/controls'
import { Badge, Card, StatCard, StatusDot } from '../components/ui/display'
import { EmptyState, ErrorState, PageSkeleton, Skeleton, useToast } from '../components/ui/feedback'
import RangeField from '../components/ui/RangeField'
import Table from '../components/ui/Table'
import { AreaSeries } from '../components/ui/chartsMore'
import TrafficMap, { MapLegend } from '../components/traffic/TrafficMap'
import api, { describeError } from '../api'
import { n0, n1 } from '../format'
import { useGet } from '../lib/useRequest'

const COLUMNS = [
  { key: 'junction', label: 'Junction', render: (r) => <span className="font-mono text-fg">{r.junction}</span> },
  { key: 'green', label: 'Green', render: (r) => <span className={`whitespace-nowrap ${r.green.includes('clearing') ? 'text-warn' : 'text-ok'}`}>{r.green.replace('North-South', 'N-S').replace('East-West', 'E-W')}</span> },
  { key: 'timer', label: 'Timer', align: 'right', render: (r) => <span className="font-mono tabular-nums">{r.timer}s</span> },
  { key: 'queue', label: 'Queue', render: (r) => <span className="font-mono tabular-nums">{r.queue}</span> },
  { key: 'forecast', label: '+30 s', render: (r) => <span className="font-mono tabular-nums text-cyan">{r.forecast}</span> },
  { key: 'preempt', label: 'Pre', align: 'center', render: (r) => (r.preempt ? <Badge tone="warn">⚡ on</Badge> : <span className="text-dim">-</span>) },
]

export default function Live() {
  const { snap, error, busy, refresh, configure, step, ambulance, reset } = useLive()
  const meta = useGet('/meta')
  const toast = useToast()
  const [demand, setDemand] = useState(1.0)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [actionError, setActionError] = useState(null)
  const stopRef = useRef(false)
  const demandTimer = useRef(null)

  useEffect(() => { if (snap) setDemand(snap.config.demand) }, [snap?.config.demand]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => { stopRef.current = true; clearTimeout(demandTimer.current) }, [])

  const guard = useCallback(async (fn) => {
    setActionError(null)
    try { return await fn() } catch (e) { setActionError(e?.message ? e : describeError(e)); return null }
  }, [])

  const runLive = useCallback(async () => {
    stopRef.current = false
    setRunning(true)
    setProgress(0)
    logEvent('ui', 'live run started (30 x 2 s)')
    setActionError(null)
    try {
      for (let i = 0; i < 30 && !stopRef.current; i++) {
        await step(2, { quiet: true })
        setProgress(i + 1)
        await new Promise((r) => setTimeout(r, 100))
      }
      logEvent('ui', stopRef.current ? 'live run stopped' : 'live run finished (60 s simulated)')
      if (!stopRef.current) toast({ title: 'Live run finished', body: '60 simulated seconds played out.' })
    } catch (e) {
      setActionError(e)
    } finally {
      setRunning(false)
    }
  }, [step, toast])

  if (error && !snap) {
    return (
      <div>
        <PageHeader title="Live control center" eyebrow="01 · live" />
        <ErrorState error={error} onRetry={refresh} title="Could not load the simulation" />
      </div>
    )
  }
  if (!snap) return <PageSkeleton />

  const { config: cfg, kpis: k, banner, junctions, queue_series: series } = snap
  const controllers = meta.data?.controllers || {}
  const lockedUi = busy || running
  const emptySeries = series.length < 2

  return (
    <div>
      <PageHeader eyebrow="01 · live" title="Live control center"
        subtitle="One shared simulation of a signalised grid. Switch the controller while it runs to see how each strategy handles the same traffic."
        actions={<span className="inline-flex items-center gap-2 font-mono text-xs text-muted"><StatusDot tone={running ? 'ok' : 'dim'} blink={running} label={running ? `running ${progress}/30` : 'paused'} /></span>} />

      <SlideUp>
        <Card title="Scenario" className="mb-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.4fr_1.2fr_auto_auto]">
            <Select label="Signal controller" value={cfg.controller} disabled={lockedUi && !running}
              onChange={(e) => guard(() => configure({ controller: e.target.value }))}
              options={Object.entries(controllers).length ? Object.entries(controllers) : [[cfg.controller, cfg.controller]]} />
            <RangeField label="Traffic demand" value={demand} min={0.4} max={2} step={0.1} format={(v) => `×${v.toFixed(1)}`} disabled={busy && !running}
              onChange={setDemand}
              onCommit={(v) => { if (Math.abs(v - cfg.demand) > 1e-6) guard(() => configure({ demand: v })) }} />
            <div className="flex flex-col justify-end">
              <Switch checked={cfg.emergencies} onChange={(v) => guard(() => configure({ emergencies: v }))} label="Emergency vehicles" />
              <p className="mt-1 text-xs text-dim">Random ambulances enter the network.</p>
            </div>
            <div className="flex flex-col justify-end text-xs text-dim">
              <span className="font-mono uppercase tracking-wider">Network</span>
              <span className="font-mono text-sm text-fg">{cfg.grid.replace('x', ' × ')}</span>
              <span>change it in the sidebar</span>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2 border-t border-line pt-4 sm:flex sm:flex-wrap">
            {running ? (
              <Button variant="danger" icon={Square} onClick={() => { stopRef.current = true }}>Stop</Button>
            ) : (
              <Button icon={Play} onClick={runLive} disabled={busy}>Run live (60 s)</Button>
            )}
            <Button variant="secondary" icon={ChevronsRight} disabled={lockedUi}
              onClick={() => guard(async () => { const d = await step(300); toast({ title: 'Skipped 5 minutes', body: `${n0(d.kpis.throughput)} vehicles completed so far.` }) })}>Skip 5 min</Button>
            <Button variant="secondary" icon={Ambulance} disabled={lockedUi}
              onClick={() => guard(async () => { const d = await ambulance(); toast({ tone: 'warn', title: 'Ambulance dispatched', body: `Entering at J${d.entry.junction}, ${d.entry.approach} approach.` }) })}>Send ambulance</Button>
            <Button variant="ghost" icon={RotateCcw} disabled={busy || running}
              onClick={() => guard(async () => { await reset(); toast({ title: 'Simulation reset', body: 'Back to 08:00:00 with an empty network.' }) })}>Reset</Button>
          </div>
          {actionError && <div className="mt-3"><ErrorState error={actionError} compact title="Action failed" onRetry={() => setActionError(null)} /></div>}
        </Card>
      </SlideUp>

      <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-5" gap={0.05}>
        <StatCard icon={Clock} label="Sim clock" value={snap.clock} sub={`demand ×${n1(k.demand_mult)} at this hour`} tone="cyan" live={running} />
        <StatCard icon={Car} label="Vehicles in network" value={k.in_network} sub={`${n0(k.queued)} queued`} tone="info" />
        <StatCard icon={Timer} label="Avg delay / veh" value={`${n0(k.avg_delay)} s`} sub={`${n0(k.throughput)} completed trips`} tone="ok" />
        <StatCard icon={Ambulance} label="Emergency delay" value={`${n1(k.emg_delay)} s`} sub={`${k.emg_served} served · ${k.emg_active} active`} tone={k.emg_active ? 'alert' : 'ok'} live={k.emg_active > 0} />
        <StatCard icon={ShieldAlert} label="Violations caught" value={k.violations} sub={`${k.red} red-light · ${k.wrong} wrong-way`} tone="warn" />
      </Stagger>

      {banner && (
        <div role="status" className={`mt-4 flex items-center gap-3 rounded-[6px] border px-4 py-2.5 text-sm ${banner.kind === 'preempt' ? 'border-alert/40 bg-alert/10 text-alert' : 'border-warn/40 bg-warn/10 text-warn'}`}>
          <AlertOctagon size={17} aria-hidden="true" />
          <span className="font-mono text-[13px]">{banner.text}</span>
        </div>
      )}

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.55fr_1fr]">
        <Card title="Road network" action={<span className="font-mono text-[11px] text-dim">{snap.map.vehicles.length} vehicles on the map</span>}>
          <div className={`rounded-[6px] bg-bg/60 p-2 ${busy && !running ? 'opacity-70' : ''} transition-opacity`}>
            <TrafficMap map={snap.map} />
          </div>
          <div className="mt-3"><MapLegend /></div>
        </Card>
        <div className="flex min-w-0 flex-col gap-4">
          <Card title="Vehicles queued (network total)" action={<Badge tone="cyan">last {series.length}s</Badge>}>
            {emptySeries ? (
              <EmptyState icon={Waypoints} title="No traffic recorded yet" body="Run the simulation to see the network queue build up and clear."
                action={<Button size="sm" icon={Play} onClick={runLive} disabled={busy || running}>Run live (60 s)</Button>} />
            ) : (
              <AreaSeries data={series} xKey="t" yKey="q" name="Queued vehicles" tone="cyan" height={210} label="Queued vehicles over time"
                valueFormat={(v) => `${v} veh`} labelFormat={(t) => `t = ${t}s`} xName="simulated seconds" />
            )}
          </Card>
          <Card title="Junction status">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-dim">queue and +30 s forecast are N/E/S/W · Pre = pre-empted</p>
            <Table columns={COLUMNS} rows={junctions} rowKey={(r) => r.junction} dense caption="Junction status"
              cards={(r) => (
                <div className="rounded border border-line bg-panel-2 p-3 text-xs">
                  <div className="mb-1 flex items-center justify-between"><span className="font-mono text-sm text-fg">{r.junction}</span>{r.preempt && <Badge tone="warn">⚡ pre-empt</Badge>}</div>
                  <div className="text-muted">{r.green} · {r.timer}s</div>
                  <div className="font-mono text-muted">queue {r.queue} → forecast {r.forecast}</div>
                </div>
              )} />
          </Card>
        </div>
      </div>
      <p className="mt-4 text-xs text-dim">
        Signals: green · clearing · red. Squares are vehicles (car, bike, bus, truck); the star is an ambulance; ⚡ marks a junction pre-empted for an emergency vehicle.
        Switch the controller while running to see the difference on the same traffic.
      </p>
    </div>
  )
}

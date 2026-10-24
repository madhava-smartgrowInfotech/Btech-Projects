import { Fuel, Gauge, Play, Siren, TrendingDown, TrendingUp } from 'lucide-react'
import { useCallback, useState } from 'react'
import api, { describeError } from '../api'
import { CTRL_KEYS, CTRL_SHORT, CTRL_VAR, n1 } from '../format'
import { logEvent } from '../lib/activity'
import { useLive } from '../lib/live'
import { SlideUp, Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Select } from '../components/ui/controls'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, ProgressBar, Skeleton, useToast } from '../components/ui/feedback'
import RangeField from '../components/ui/RangeField'
import Table from '../components/ui/Table'
import { BarsChart, BoxPlot, LinesChart } from '../components/ui/chartsMore'
import { ChartLegend } from '../components/ui/charts'

const DURATIONS = [[600, '10 min'], [900, '15 min'], [1200, '20 min'], [1800, '30 min'], [2700, '45 min'], [3600, '60 min']]
// results survive navigating away and back, like the Streamlit session did
let remembered = { form: { seconds: 1800, demand: 1.2, seeds: 3, start_hour: 8 }, result: null, sweep: null }

export default function Benchmark() {
  const { snap } = useLive()
  const toast = useToast()
  const [form, setForm] = useState(remembered.form)
  const [result, setResult] = useState(remembered.result)
  const [sweep, setSweep] = useState(remembered.sweep)
  const [running, setRunning] = useState(false)
  const [sweeping, setSweeping] = useState(false)
  const [error, setError] = useState(null)
  const [sweepError, setSweepError] = useState(null)

  const grid = snap?.config.grid || '2x2'
  const useMl = snap?.config.use_ml ?? true
  const set = (k) => (v) => setForm((f) => { const n = { ...f, [k]: v }; remembered.form = n; return n })

  const run = useCallback(async () => {
    setRunning(true)
    setError(null)
    logEvent('pipeline', `benchmark: 4 controllers x ${form.seeds} seeds x ${form.seconds / 60} min on ${grid}`)
    try {
      const r = await api.post('/benchmark', { grid, use_ml: useMl, ...form })
      remembered.result = r.data
      setResult(r.data)
      toast({ title: 'Benchmark complete', body: `Advanced controller: −${r.data.kpis.d_fixed}% delay vs fixed-time.` })
    } catch (e) {
      setError(describeError(e))
    } finally {
      setRunning(false)
    }
  }, [form, grid, useMl, toast])

  const runSweep = useCallback(async () => {
    setSweeping(true)
    setSweepError(null)
    logEvent('pipeline', 'demand sweep: 4 controllers x 5 demand levels')
    try {
      const r = await api.post('/benchmark/sweep', { grid, use_ml: useMl })
      remembered.sweep = r.data
      setSweep(r.data)
    } catch (e) {
      setSweepError(describeError(e))
    } finally {
      setSweeping(false)
    }
  }, [grid, useMl])

  const k = result?.kpis
  const ctrls = result ? CTRL_KEYS.map((c) => ({ key: c, ...result.controllers[c], short: CTRL_SHORT[c] })) : []
  const delayRows = ctrls.map((c) => ({ name: c.short, delay: c.delay_mean, std: c.delay_std, color: CTRL_VAR[c.key] }))
  const emgRows = ctrls.map((c) => ({ name: c.short, delay: c.emg_mean, std: c.emg_std, color: CTRL_VAR[c.key] }))
  const queueLen = ctrls[0]?.queue.length || 0
  const queueRows = Array.from({ length: queueLen }, (_, i) => ({ m: +((i * 10) / 60).toFixed(2), ...Object.fromEntries(ctrls.map((c) => [c.key, c.queue[i]])) }))
  const sweepRows = sweep ? sweep.levels.map((d, i) => ({ d, ...Object.fromEntries(CTRL_KEYS.map((c) => [c, sweep.series[c][i]])) })) : []
  const tableCols = result ? [
    { key: 'controller', label: 'Controller', render: (r) => <span className="text-fg">{r.controller}</span> },
    ...result.columns.map((c) => ({ key: c, label: c, align: 'right', render: (r) => <span className="font-mono tabular-nums">{r[c]}</span> })),
  ] : []

  return (
    <div>
      <PageHeader eyebrow="02 · benchmark" title="Controller benchmark"
        subtitle="Identical traffic, four strategies. Each controller faces exactly the same vehicles, emergency events and violators, replacing the base paper's SUMO validation with the built-in simulator." />

      <SlideUp>
        <Card title="Settings" action={<span className="font-mono text-[11px] text-dim">{grid.replace('x', ' × ')} · ML {useMl ? 'on' : 'off'}</span>}>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Select label="Duration" value={form.seconds} onChange={(e) => set('seconds')(Number(e.target.value))} options={DURATIONS} disabled={running} />
            <RangeField label="Demand" value={form.demand} min={0.5} max={1.8} step={0.1} format={(v) => `×${v.toFixed(1)}`} onChange={set('demand')} disabled={running} />
            <RangeField label="Random seeds" value={form.seeds} min={1} max={5} step={1} onChange={set('seeds')} disabled={running} />
            <RangeField label="Start hour" value={form.start_hour} min={0} max={23} step={1} format={(v) => `${String(v).padStart(2, '0')}:00`} onChange={set('start_hour')} disabled={running} />
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-line pt-4">
            <Button icon={Play} loading={running} onClick={run}>{result ? 'Run again' : 'Run benchmark'}</Button>
            <span className="text-xs text-dim">Simulates 4 controllers × {form.seeds} seed{form.seeds > 1 ? 's' : ''}; a few seconds on this machine.</span>
          </div>
        </Card>
      </SlideUp>

      <div className="mt-4 space-y-4" aria-live="polite">
        {error && <ErrorState error={error} title="Benchmark failed" onRetry={run} />}

        {running && !result && (
          <div className="space-y-3" aria-busy="true" aria-label="Running benchmark">
            <ProgressBar value={100} label="Simulating 4 controllers…" />
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
            <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
          </div>
        )}

        {!result && !running && !error && (
          <Card><EmptyState icon={Gauge} title="No benchmark yet" body="Choose the settings above and run the benchmark to compare fixed-time, adaptive, emergency-aware and the advanced coordinated controller on identical traffic."
            action={<Button icon={Play} onClick={run}>Run benchmark</Button>} /></Card>
        )}

        {result && (
          <div className={running ? 'opacity-60 transition-opacity' : 'transition-opacity'}>
            <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4" gap={0.05}>
              <StatCard icon={TrendingDown} label="Delay vs fixed-time" value={`−${k.d_fixed}%`} sub="advanced vs traditional" tone="ok" />
              <StatCard icon={k.d_paper >= 0 ? TrendingDown : TrendingUp} label="Delay vs base paper" value={`${k.d_paper >= 0 ? '−' : '+'}${Math.abs(k.d_paper)}%`} sub="advanced vs emergency-aware" tone={k.d_paper >= 0 ? 'ok' : 'warn'} />
              <StatCard icon={Siren} label="Emergency delay" value={`−${k.e_fixed}%`} sub={`${k.emg_ours}s vs ${k.emg_base}s`} tone="ok" />
              <StatCard icon={Fuel} label="Fuel saved" value={`${k.fuel} L`} sub={`${k.co2} kg CO₂ avoided`} tone="cyan" />
            </Stagger>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <Card title="Avg delay / vehicle (s)" action={<span className="font-mono text-[11px] text-dim">mean ± std over {result.settings.seeds} seed(s)</span>}>
                <BarsChart data={delayRows} xKey="name" bars={[{ key: 'delay', label: 'Avg delay (s)', color: 'var(--ok)' }]} colorKey="color" errorKey="std" topLabels
                  valueFormat={(v) => n1(v)} label="Average delay per vehicle by controller" height={280} />
              </Card>
              <Card title="Emergency delay (s)">
                <BarsChart data={emgRows} xKey="name" bars={[{ key: 'delay', label: 'Emergency delay (s)', color: 'var(--alert)' }]} colorKey="color" errorKey="std" topLabels
                  valueFormat={(v) => n1(v)} label="Emergency vehicle delay by controller" height={280} />
              </Card>
              <Card title="Queued vehicles over time">
                <LinesChart data={queueRows} xKey="m" xName="minutes" label="Queued vehicles over time per controller" height={290}
                  lines={ctrls.map((c) => ({ key: c.key, label: c.short, color: CTRL_VAR[c.key], width: c.key === 'advanced' ? 3 : 1.6 }))}
                  valueFormat={(v) => `${n1(v)} veh`} labelFormat={(m) => `minute ${m}`} />
              </Card>
              <Card title="Emergency-vehicle delay distribution (s)">
                <BoxPlot groups={ctrls.map((c) => ({ label: c.short, color: CTRL_VAR[c.key], values: c.emergency_delays.filter((v) => v !== null) }))}
                  label="Emergency delay distribution per controller" height={290} yName="seconds" />
                <ChartLegend items={[{ label: 'box = IQR, bar = median, ◆ = mean', color: 'var(--muted)' }]} />
              </Card>
            </div>

            <Card title="Full results (mean over seeds)" className="mt-4">
              <Table columns={tableCols} rows={result.table} rowKey={(r) => r.controller} caption="Benchmark results by controller" dense />
            </Card>

            <Card title="Demand sweep" className="mt-4"
              action={<Button size="sm" variant="secondary" loading={sweeping} onClick={runSweep}>{sweep ? 'Run again' : 'Run demand sweep'}</Button>}>
              <p className="mb-3 text-sm text-muted">How each controller degrades as traffic grows (demand ×0.6 to ×1.8, 20 simulated minutes each).</p>
              {sweepError && <ErrorState error={sweepError} compact title="Sweep failed" onRetry={runSweep} />}
              {sweeping && !sweep && <Skeleton className="h-64" />}
              {!sweep && !sweeping && !sweepError && (
                <EmptyState icon={TrendingUp} title="Sweep not run" body="Run the sweep to see delay against demand for every controller." />
              )}
              {sweep && (
                <LinesChart data={sweepRows} xKey="d" xName="demand multiplier" yName="avg delay (s)" height={300} label="Average delay against demand"
                  lines={CTRL_KEYS.map((c) => ({ key: c, label: CTRL_SHORT[c], color: CTRL_VAR[c], dots: true, width: c === 'advanced' ? 3 : 1.6 }))}
                  valueFormat={(v) => `${n1(v)} s`} labelFormat={(d) => `demand ×${d}`} />
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

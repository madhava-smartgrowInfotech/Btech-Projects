import { AlertTriangle, BrainCircuit, Database, Play, Target, TrendingDown, Waypoints } from 'lucide-react'
import { useState } from 'react'
import { describeError } from '../api'
import { logEvent } from '../lib/activity'
import { useLive } from '../lib/live'
import { useGet } from '../lib/useRequest'
import { Stagger } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button } from '../components/ui/controls'
import { Card, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, ProgressBar, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { BarsChart, HBars, ScatterPlot } from '../components/ui/chartsMore'

const FEATURE_LABEL = {
  queue: 'queue now', pcu_queue: 'PCU queue', queue_lag10: 'queue 10 s ago', queue_lag30: 'queue 30 s ago', inflow_30s: 'inflow (30 s)',
  inbound_15s: 'inbound (15 s)', is_green: 'is green', green_time: 'green time', is_entry: 'entry road', sin_day: 'time of day (sin)', cos_day: 'time of day (cos)',
}

export default function Prediction() {
  const { snap, simulate, busy } = useLive()
  const toast = useToast()
  const model = useGet('/prediction', { retryOn503: 12 })
  const forecast = useGet('/prediction/live', { deps: [snap?.t] })
  const [simError, setSimError] = useState(null)

  async function simulateNow() {
    setSimError(null)
    try {
      await simulate()
      logEvent('ui', 'simulated 3 minutes for the forecast')
      toast({ title: 'Simulated 3 minutes', body: 'Forecasts are now based on the live network.' })
    } catch (e) {
      setSimError(e?.message ? e : describeError(e))
    }
  }

  const d = model.data
  const training = model.loading || (model.error?.status === 503)
  const imp = d?.importance.map((i) => ({ ...i, feature: FEATURE_LABEL[i.feature] || i.feature })) || []
  const f = forecast.data

  return (
    <div>
      <PageHeader eyebrow="04 · prediction" title="Traffic prediction"
        subtitle="A gradient-boosted model forecasts each approach's queue 30 seconds ahead, trained on simulated junction data, so the advanced controller can give green proactively." />

      {model.error && model.error.status !== 503 && <ErrorState error={model.error} title="Prediction model unavailable" onRetry={model.reload} />}

      {training && !d && !(model.error && model.error.status !== 503) && (
        <div className="space-y-3" aria-busy="true">
          <ProgressBar value={100} label="Training the traffic-prediction model (first start only, about 10 s)…" />
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
          <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-80" /><Skeleton className="h-80" /></div>
        </div>
      )}

      {d && (
        <>
          <Stagger className="grid grid-cols-2 gap-3 lg:grid-cols-4" gap={0.05}>
            <StatCard icon={Database} label="Training samples" value={d.kpis.samples} sub="from simulated junction data" tone="info" />
            <StatCard icon={Target} label="MAE (GBM)" value={`${d.kpis.mae} veh`} sub="mean absolute error" tone="ok" />
            <StatCard icon={BrainCircuit} label="R² (GBM)" value={`${d.kpis.r2}`} sub="variance explained" tone="ok" />
            <StatCard icon={TrendingDown} label="vs persistence" value={`−${d.kpis.vs_persistence}% error`} sub={'beats "queue stays the same"'} tone="cyan" />
          </Stagger>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card title="Predicted vs actual (held-out test set)">
              <ScatterPlot data={d.scatter} xKey="actual" yKey="predicted" xName="actual queue in 30 s" yName="predicted" ideal={d.ideal_max} label="Predicted against actual queue length" height={320} />
              <p className="mt-1 text-xs text-dim">{d.scatter.length} random test points · dashed line = perfect forecast.</p>
            </Card>
            <Card title="What the model relies on">
              <HBars data={imp} labelKey="feature" valueKey="value" name="Importance" tone="ok" height={320} valueFormat={(v) => Number(v).toFixed(3)} label="Feature importance" />
            </Card>
          </div>

          <Card title="Model comparison" className="mt-4">
            <Table rows={d.metrics} rowKey={(r) => r.model} dense caption="Model comparison"
              columns={[
                { key: 'model', label: 'Model', render: (r) => <span className={r.model.includes('used') ? 'text-ok' : 'text-fg'}>{r.model}</span> },
                { key: 'mae', label: 'MAE (veh)', align: 'right', render: (r) => <span className="font-mono tabular-nums">{r.mae}</span> },
                { key: 'r2', label: 'R²', align: 'right', render: (r) => <span className="font-mono tabular-nums">{r.r2}</span> },
              ]} />
          </Card>
        </>
      )}

      <Card title="Live forecast for the running simulation" className="mt-4"
        action={f?.available ? <span className="font-mono text-[11px] text-dim">at {f.clock}</span> : null}>
        {forecast.loading && !f && <Skeleton className="h-64" />}
        {forecast.error && forecast.error.status !== 503 && <ErrorState error={forecast.error} compact onRetry={forecast.reload} />}
        {forecast.error?.status === 503 && <p className="text-sm text-muted">Waiting for the model to finish training…</p>}
        {f && !f.available && (
          <EmptyState icon={Waypoints} title="No live traffic to forecast yet"
            body="Run the live simulation for a minute on Live control, or simulate three minutes here."
            action={<Button icon={Play} loading={busy} onClick={simulateNow}>Simulate 3 minutes now</Button>} />
        )}
        {simError && <div className="mt-3"><ErrorState error={simError} compact title="Simulation failed" onRetry={simulateNow} /></div>}
        {f?.available && (
          <>
            <BarsChart data={f.bars} xKey="label" height={290} legend label={`Queue per approach at ${f.clock}`}
              bars={[{ key: 'now', label: 'Queue now', color: 'var(--dim)' }, { key: 'forecast', label: 'Forecast +30 s', color: 'var(--hot)' }]}
              valueFormat={(v) => `${v} veh`} />
            <div role="status" className="mt-3 flex items-start gap-3 rounded-[6px] border border-warn/40 bg-warn/10 px-4 py-2.5 text-sm text-warn">
              <AlertTriangle size={17} className="mt-0.5 shrink-0" aria-hidden="true" />
              <span>Highest predicted build-up: <strong className="font-mono">J{f.worst.junction} · {f.worst.approach}</strong> approach ({f.worst.now} → {f.worst.forecast} vehicles). The advanced controller gives it green proactively.</span>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}

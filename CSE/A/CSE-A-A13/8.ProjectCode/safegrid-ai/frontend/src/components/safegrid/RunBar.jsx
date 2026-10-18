import { useEffect, useRef, useState } from 'react'
import { Play, RotateCcw, Square, StepForward } from 'lucide-react'
import { useSimulation } from '../../hooks/useSimulation'
import { PROVIDERS, isFinished, titleize } from '../../lib/format'
import { Button } from '../ui/controls'
import { Input, Select } from '../ui/controls'
import { Card } from '../ui/display'
import { ProgressBar, Skeleton } from '../ui/feedback'

const SPEEDS = [
  { value: '1.2', label: 'Slow' },
  { value: '0.6', label: 'Normal' },
  { value: '0.2', label: 'Fast' },
  { value: '0', label: 'Instant' },
]

/** Run controls shown above every console screen: pick scenario / brain / seed, then start, step, stop or reset. */
export default function RunBar() {
  const { status, scenarios, start, stop, reset, step, busy, ready, error, refresh } = useSimulation()
  const [cfg, setCfg] = useState({ scenario_id: 'normal', provider: 'mock', seed: 42, step_delay_s: '0.6' })
  const synced = useRef(false)

  // adopt the backend's current configuration once, so the controls reflect the run that is already loaded
  useEffect(() => {
    if (!status || synced.current) return
    synced.current = true
    setCfg((c) => ({ ...c, scenario_id: status.scenario_id || c.scenario_id, provider: status.provider?.provider || c.provider, seed: status.seed ?? c.seed }))
  }, [status])

  if (!ready) {
    return (
      <Card className="runbar" spotlight={false} aria-busy="true" aria-label="Loading run controls">
        <Skeleton height={44} />
      </Card>
    )
  }

  const running = status?.status === 'running'
  const finished = isFinished(status)
  const dirty = !!status && (status.scenario_id !== cfg.scenario_id || status.provider?.provider !== cfg.provider || Number(status.seed) !== Number(cfg.seed))
  const fresh = !status || status.step === 0 || finished || dirty
  const total = status?.total_steps || 0
  const payload = { scenario_id: cfg.scenario_id, provider: cfg.provider, seed: Number(cfg.seed) || 0, step_delay_s: Number(cfg.step_delay_s) }
  const set = (k) => (e) => setCfg((c) => ({ ...c, [k]: e.target.value }))
  const scenarioOptions = scenarios.length ? scenarios.map((s) => ({ value: s.id, label: s.name })) : [{ value: cfg.scenario_id, label: titleize(cfg.scenario_id) }]
  const locked = running || !!busy

  return (
    <Card className="runbar" spotlight={false} role="region" aria-label="Run controls">
      <div className="runbar-fields">
        <Select label="Scenario" options={scenarioOptions} value={cfg.scenario_id} onChange={set('scenario_id')} disabled={locked} />
        <Select label="Agent brain" options={PROVIDERS} value={cfg.provider} onChange={set('provider')} disabled={locked} />
        <Input label="Seed" type="number" value={cfg.seed} onChange={set('seed')} disabled={locked} />
        <Select label="Playback" options={SPEEDS} value={cfg.step_delay_s} onChange={set('step_delay_s')} disabled={locked} />
      </div>
      <div className="runbar-actions">
        <Button variant="primary" icon={Play} disabled={running || (busy && busy !== 'start the run')} loading={busy === 'start the run'} onClick={() => start(payload, !fresh)}>
          {fresh ? 'Start' : 'Resume'}
        </Button>
        <Button icon={StepForward} disabled={locked || finished || dirty} loading={busy === 'advance one step'} onClick={step} title={finished ? 'The run has finished - reset to go again' : dirty ? 'Reset to apply the new settings first' : undefined}>
          Step
        </Button>
        <Button icon={Square} disabled={!running} loading={busy === 'stop the run'} onClick={stop}>
          Stop
        </Button>
        <Button variant="ghost" icon={RotateCcw} disabled={running || !!busy} loading={busy === 'reset the run'} onClick={() => reset(payload)}>
          Reset
        </Button>
      </div>
      <div className="runbar-progress">
        {error ? (
          <div className="runbar-error" role="alert">
            <span>{error}</span>
            <Button size="sm" onClick={refresh}>
              Retry
            </Button>
          </div>
        ) : (
          <ProgressBar
            value={status?.step || 0}
            max={Math.max(total, 1)}
            label={finished ? 'Run finished' : running ? 'Running' : 'Ready'}
            valueLabel={`step ${status?.step ?? 0} of ${total} · ${status?.time ?? '--:--'}`}
          />
        )}
        {dirty && !running && !error && <p className="faint">Settings changed - Start or Reset to load a new run.</p>}
      </div>
    </Card>
  )
}

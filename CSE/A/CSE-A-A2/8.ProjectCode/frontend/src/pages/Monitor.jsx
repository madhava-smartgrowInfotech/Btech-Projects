import { Play, Square } from 'lucide-react'
import { Button, Card, PageHeader, Switch } from '../components/ui'
import { PageTransition } from '../components/motion'
import { EventLog } from '../features/EventLog'
import { PipelineError } from '../features/ApiError'
import { ResultPanel } from '../features/ResultPanel'
import { SensorChart } from '../features/SensorChart'
import { SCENARIOS } from '../lib/format'
import { useMonitor } from '../state/MonitorContext'

export default function Monitor() {
  const m = useMonitor()
  return (
    <PageTransition>
      <PageHeader
        eyebrow="Live monitor"
        title="Sensor feed"
        description="No phone is attached, so readings are simulated by the backend and sent through the accident and severity models."
        actions={
          <Button
            variant={m.live ? 'danger' : 'primary'}
            icon={m.live ? Square : Play}
            onClick={() => m.setLive(!m.live)}
            aria-pressed={m.live}
          >
            {m.live ? 'Stop live monitoring' : 'Start live monitoring'}
          </Button>
        }
      />
      <PipelineError />
      <div className="grid" style={{ '--gap': '24px' }}>
        <Card title="Scenarios" actions={m.live && <span className="badge badge-live"><span className="badge-dot" /> Streaming every 1.5s</span>}>
          <div className="stack">
            <p className="small muted">Each button fetches one synthetic reading from the backend and runs detection on it. Moderate and severe results start the 15 second confirmation.</p>
            <div className="row" role="group" aria-label="Scenario">
              {SCENARIOS.map((s) => (
                <Button key={s.id} variant={s.tone === 'danger' ? 'danger' : 'secondary'} size="sm" disabled={m.busy || Boolean(m.pending)} onClick={() => m.runScenario(s.id)}>
                  {s.label}
                </Button>
              ))}
            </div>
            <Switch label="Live monitoring" checked={m.live} onChange={m.setLive} />
          </div>
        </Card>
        <div className="grid grid-2" style={{ '--gap': '24px', alignItems: 'start' }}>
          <div className="stack" style={{ '--gap': '24px' }}>
            <ResultPanel result={m.result} busy={m.busy} />
            <EventLog events={m.events} />
          </div>
          <SensorChart data={m.history} />
        </div>
      </div>
    </PageTransition>
  )
}

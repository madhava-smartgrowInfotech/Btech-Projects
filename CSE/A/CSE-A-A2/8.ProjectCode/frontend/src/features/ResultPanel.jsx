import { Activity, CarFront, CheckCircle2, TriangleAlert } from 'lucide-react'
import { Badge, Card, EmptyState, KeyValueList, ProgressBar, Skeleton } from '../components/ui'
import { fmtNum, fmtPct, SEVERITY } from '../lib/format'

const ICON = { None: CheckCircle2, Minor: TriangleAlert, Moderate: TriangleAlert, Severe: CarFront }
const TONE = { None: 'lime', Minor: undefined, Moderate: undefined, Severe: 'coral' }

/** Detection result for the latest reading. `emptyAction` is shown when nothing has been run yet. */
export function ResultPanel({ result, busy, emptyAction }) {
  if (!result) {
    return (
      <Card title="Detection result">
        {busy ? (
          <div className="stack" role="status" aria-label="Running detection">
            <Skeleton height={64} width={64} />
            <Skeleton height={30} width="70%" />
            <Skeleton height={16} />
          </div>
        ) : (
          <EmptyState icon={Activity} title="Waiting for a reading" action={emptyAction}>
            Run a scenario, start live monitoring or submit manual values. The model's verdict appears here.
          </EmptyState>
        )}
      </Card>
    )
  }
  const sev = SEVERITY[result.severity_label] || SEVERITY.None
  const Icon = ICON[result.severity_label] || CheckCircle2
  const f = result.features_used
  return (
    <Card title="Detection result" tone={TONE[result.severity_label]} aria-live="polite" aria-busy={busy || undefined}>
      <div className="stack" style={{ '--gap': '14px' }}>
        <div className="row" style={{ '--gap': '14px', flexWrap: 'nowrap' }}>
          <div className="state-icon" aria-hidden="true" style={{ background: sev.color, color: '#111', flex: 'none' }}>
            <Icon size={30} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h3 className="display-sm" style={{ overflowWrap: 'anywhere' }}>
              {result.accident_detected ? `Accident detected` : 'No accident'}
            </h3>
            <Badge tone={sev.tone}>Severity: {result.severity_label}</Badge>
          </div>
        </div>
        <div>
          <div className="row-between small" style={{ marginBottom: 6 }}>
            <span>Accident probability</span>
            <strong className="mono">{fmtPct(result.confidence)}</strong>
          </div>
          <ProgressBar value={result.confidence} label="Accident probability" tone={result.accident_detected ? 'coral' : undefined} />
        </div>
        <KeyValueList
          items={[
            { label: 'Model', value: result.model_source === 'trained_ml_model' ? 'Trained ML model' : 'Rule-based fallback' },
            { label: 'Scenario', value: result.source },
            { label: 'Acc. magnitude', value: `${fmtNum(f.acc_magnitude)} m/s²` },
            { label: 'Gyro magnitude', value: `${fmtNum(f.gyro_magnitude)} rad/s` },
            { label: 'Speed change', value: `${fmtNum(f.speed_change, 1)} km/h` },
            { label: 'Last update', value: result.at },
          ]}
        />
      </div>
    </Card>
  )
}

import { lazy, Suspense } from 'react'
import { LineChart } from 'lucide-react'
import { Card, EmptyState, Skeleton } from '../components/ui'

// Recharts is heavy: load it only when the chart is first shown.
const LineTrace = lazy(() => import('../components/ui/LineTrace').then((m) => ({ default: m.LineTrace })))

const SERIES = [
  { key: 'acc', name: 'Acc. magnitude', unit: 'm/s²', color: '#ff5c39' },
  { key: 'gyro', name: 'Gyro magnitude', unit: 'rad/s', color: '#7cc6ff' },
]

/** Rolling trace of the last 40 readings. */
export function SensorChart({ data }) {
  return (
    <Card title="Sensor trace" actions={<span className="tiny mono muted">last {data.length}/40</span>}>
      {data.length === 0 ? (
        <EmptyState icon={LineChart} title="No readings yet">
          Pick a scenario above or start live monitoring to draw the accelerometer and gyroscope trace.
        </EmptyState>
      ) : (
        <Suspense fallback={<Skeleton height={260} />}>
          <div role="img" aria-label={`Line chart of the last ${data.length} readings. Latest: acceleration ${data[data.length - 1].acc} metres per second squared, gyroscope ${data[data.length - 1].gyro} radians per second.`}>
            <LineTrace data={data} xKey="t" series={SERIES} />
          </div>
        </Suspense>
      )}
    </Card>
  )
}

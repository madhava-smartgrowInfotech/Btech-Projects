import { Alert } from './ui/Feedback'

/** Capacity warnings from the forecast. alerts: [{level: 'critical'|'warning', message, facility, ward, day}] */
export default function AlertList({ alerts, empty = 'No capacity warnings in the forecast window.' }) {
  if (!alerts?.length) return <Alert tone="success">{empty}</Alert>
  return (
    <div className="stack" style={{ '--gap': '10px' }}>
      {alerts.map((a) => (
        <Alert key={`${a.facility}-${a.ward}-${a.day}-${a.level}`} tone={a.level === 'critical' ? 'error' : 'warning'}>
          <strong>{a.level === 'critical' ? 'Over capacity. ' : 'Early warning. '}</strong>
          {a.message}
        </Alert>
      ))}
    </div>
  )
}

import { ListChecks } from 'lucide-react'
import { Card, EmptyState, Timeline } from '../components/ui'

/** Newest-first log of the last 25 pipeline events. */
export function EventLog({ events }) {
  const items = events.map((e) => ({
    key: e.id,
    title: e.text,
    meta: e.at,
    tone: e.level === 'None' ? 'ok' : e.level === 'Severe' ? 'bad' : undefined,
  }))
  return (
    <Card title="Event log" actions={<span className="tiny mono muted">{events.length}/25</span>}>
      {events.length === 0 ? (
        <EmptyState icon={ListChecks} title="No events yet">
          Every reading, cancelled alert and dispatch is recorded here.
        </EmptyState>
      ) : (
        <div style={{ maxHeight: 340, overflowY: 'auto', paddingRight: 4 }} data-lenis-prevent tabIndex={0} role="region" aria-label="Event log entries">
          <Timeline items={items} />
        </div>
      )}
    </Card>
  )
}

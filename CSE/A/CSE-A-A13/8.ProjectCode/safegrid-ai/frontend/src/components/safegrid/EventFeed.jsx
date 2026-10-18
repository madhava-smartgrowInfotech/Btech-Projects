import { Radio } from 'lucide-react'
import { ACTION_LABEL, kw } from '../../lib/format'
import { Timeline } from '../ui/display'
import { EmptyState } from '../ui/feedback'
import { ShieldBadge } from './badges'

const TONE = { agent_action: 'info', safety_intervention: 'warn', conflict_detected: 'warn', simulation_error: 'danger', simulation_complete: 'safe' }

function describe(ev) {
  const d = ev.data || {}
  switch (ev.type) {
    case 'agent_action':
      return {
        title: (
          <>
            <strong>{d.agent_id}</strong> proposed {ACTION_LABEL[d.proposal?.action_type] || d.proposal?.action_type} {kw(d.proposal?.power_kw)}
          </>
        ),
        meta: (
          <>
            <ShieldBadge status={d.shield_status} /> executed {kw(d.executed_power_kw)}
          </>
        ),
      }
    case 'safety_intervention':
      return { title: <><strong>Shield {d.status}</strong> {d.agent_id}</>, meta: (d.violations || []).map((v) => v.code).join(', ') || undefined }
    case 'conflict_detected':
      return { title: <><strong>Conflict</strong> {d.type}</>, meta: d.detail }
    case 'grid_update':
      return { title: 'Grid updated', meta: `min voltage ${d.grid?.totals?.min_voltage_pu} pu · worst line ${d.grid?.totals?.max_line_loading_pct}%` }
    case 'simulation_started':
      return { title: `Simulation started (${d.steps} steps)` }
    case 'simulation_complete':
      return { title: 'Simulation complete' }
    case 'simulation_stopped':
      return { title: 'Simulation stopped' }
    case 'simulation_error':
      return { title: <strong>Simulation error</strong>, meta: d.error }
    default:
      return { title: ev.type }
  }
}

export const FEED_TYPES = ['agent_action', 'safety_intervention', 'conflict_detected', 'simulation_started', 'simulation_complete', 'simulation_stopped', 'simulation_error']

/** Newest-first feed of live WebSocket events (and the stored event log for the current run). */
export default function EventFeed({ events, types = FEED_TYPES, limit = 40 }) {
  const list = events.filter((e) => types.includes(e.type)).slice(0, limit)
  if (!list.length) {
    return <EmptyState icon={Radio} title="No events yet">Start or step the simulation and agent decisions, shield interventions and conflicts will appear here as they happen.</EmptyState>
  }
  return (
    <div className="feed-scroll">
      <Timeline
        items={list.map((ev, i) => {
          const d = describe(ev)
          return { key: `${ev.timestamp}-${i}`, tone: TONE[ev.type], title: d.title, meta: [ev.data?.time, d.meta].filter(Boolean).length ? <>{ev.data?.time ? `${ev.data.time} · ` : ''}{d.meta}</> : undefined }
        })}
      />
    </div>
  )
}

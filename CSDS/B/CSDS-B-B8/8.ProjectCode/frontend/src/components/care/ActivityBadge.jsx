import { activityColor, humanize } from '../../lib/format'

export default function ActivityBadge({ activity }) {
  const c = activityColor(activity)
  return (
    <span className="badge act-badge" style={{ '--c': c }}>
      <span className="dot" aria-hidden="true" style={{ background: c }} />
      {humanize(activity || 'unknown')}
    </span>
  )
}

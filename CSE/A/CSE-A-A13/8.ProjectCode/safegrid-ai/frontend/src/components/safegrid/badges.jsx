import { Badge } from '../ui/display'
import { SHIELD, SOURCE_LABEL, SOURCE_TONE } from '../../lib/format'

export function ShieldBadge({ status }) {
  const s = SHIELD[status]
  if (!s) return <Badge>{status || '-'}</Badge>
  return (
    <Badge tone={s.tone} dot>
      {s.label}
    </Badge>
  )
}

export function SourceBadge({ source }) {
  if (!source) return null
  return <Badge tone={SOURCE_TONE[source] || 'neutral'}>{SOURCE_LABEL[source] || source}</Badge>
}

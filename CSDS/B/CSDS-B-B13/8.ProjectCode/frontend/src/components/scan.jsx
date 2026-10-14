import { Badge } from './ui'
import { GRADE_TONE, SEVERITY_TONE, titleize } from '../lib/format'

// Status of a scan as the API reports it: pending, running, done or error.
export function StatusBadge({ status, progress }) {
  if (status === 'done') return <Badge tone="safe" dot>Done</Badge>
  if (status === 'error') return <Badge tone="danger" dot>Failed</Badge>
  if (status === 'running') return <Badge tone="info" dot>Running {progress}%</Badge>
  return <Badge dot>Queued</Badge>
}

export function GradeBadge({ grade }) {
  return <Badge tone={GRADE_TONE[grade] || 'neutral'}>{grade || '-'}</Badge>
}

export function SeverityBadge({ severity }) {
  return <Badge tone={SEVERITY_TONE[severity] || 'neutral'}>{titleize(severity || '')}</Badge>
}

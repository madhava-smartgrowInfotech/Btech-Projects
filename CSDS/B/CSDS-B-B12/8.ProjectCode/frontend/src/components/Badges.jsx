import { Badge } from './ui/Display.jsx'
import { MODALITY_LABEL } from '../lib/product.js'

const SEVERITY_TONE = { None: 'pass', Mild: 'upcoming', Moderate: 'info', Severe: 'blocked' }

export function SeverityBadge({ value }) {
  return <Badge tone={SEVERITY_TONE[value]}>{value || '—'}</Badge>
}

export function ModalityBadge({ value }) {
  return <Badge tone="info">{MODALITY_LABEL[value] || value}</Badge>
}

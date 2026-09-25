import { Badge } from '@/components/ui/Badge'

const SEVERITY_COLOR = {
  low: 'emerald',
  medium: 'amber',
  high: 'rose',
} as const

export function SeverityBadge({ severity }: { severity: string }) {
  const color = SEVERITY_COLOR[severity as keyof typeof SEVERITY_COLOR] ?? 'slate'
  return (
    <Badge color={color}>
      <span className={`h-1.5 w-1.5 rounded-full bg-current`} />
      {severity.charAt(0).toUpperCase() + severity.slice(1)} severity
    </Badge>
  )
}

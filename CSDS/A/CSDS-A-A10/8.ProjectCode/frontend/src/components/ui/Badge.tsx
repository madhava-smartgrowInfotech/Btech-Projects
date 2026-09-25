import { motion } from 'framer-motion'

import { cn } from '@/lib/utils'
import type { Priority, VisitStatus } from '@/types'

const PRIORITY_STYLES: Record<Priority, string> = {
  critical: 'bg-red-500/15 text-red-400 ring-1 ring-red-500/30',
  urgent: 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30',
  normal: 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/30',
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide',
        PRIORITY_STYLES[priority],
      )}
    >
      {priority === 'critical' && (
        <span className="relative flex h-1.5 w-1.5">
          <motion.span
            className="absolute inline-flex h-full w-full rounded-full bg-red-400"
            animate={{ scale: [1, 2.2], opacity: [0.8, 0] }}
            transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }}
          />
          <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-red-400" />
        </span>
      )}
      {priority}
    </span>
  )
}

const STATUS_LABELS: Record<VisitStatus, string> = {
  waiting: 'Waiting',
  in_consultation: 'In Consultation',
  lab_pending: 'Lab Pending',
  lab_in_progress: 'Lab In Progress',
  pharmacy: 'Pharmacy',
  admitted_ward: 'Admitted · Ward',
  admitted_icu: 'Admitted · ICU',
  discharged: 'Discharged',
  cancelled: 'Cancelled',
}

const STATUS_STYLES: Record<VisitStatus, string> = {
  waiting: 'bg-ink-600/60 text-ink-200',
  in_consultation: 'bg-brand-500/20 text-brand-300',
  lab_pending: 'bg-violet-500/15 text-violet-300',
  lab_in_progress: 'bg-violet-500/25 text-violet-200',
  pharmacy: 'bg-cyan-500/15 text-cyan-300',
  admitted_ward: 'bg-teal-500/15 text-teal-300',
  admitted_icu: 'bg-rose-500/15 text-rose-300',
  discharged: 'bg-ink-700 text-ink-400',
  cancelled: 'bg-ink-700 text-ink-500 line-through',
}

export function StatusBadge({ status }: { status: VisitStatus }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium',
        STATUS_STYLES[status],
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  )
}

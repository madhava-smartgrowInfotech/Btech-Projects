import { motion } from 'framer-motion'
import { Clock } from 'lucide-react'

import { Avatar } from '@/components/ui/Avatar'
import { PriorityBadge, StatusBadge } from '@/components/ui/Badge'
import { formatMinutes } from '@/lib/utils'
import type { Visit } from '@/types'

export function VisitCard({
  visit,
  onClick,
  trailing,
}: {
  visit: Visit
  onClick?: () => void
  trailing?: React.ReactNode
}) {
  return (
    <motion.button
      layout
      layoutId={visit.id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      whileHover={{ scale: 1.005 }}
      onClick={onClick}
      className="flex w-full items-center gap-3.5 rounded-xl border border-white/8 bg-ink-850/60 p-3.5 text-left transition-colors hover:border-brand-400/30 hover:bg-ink-800/70"
    >
      <Avatar name={visit.patient.name} size={38} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-semibold text-white">{visit.patient.name}</p>
          <span className="shrink-0 font-mono text-[11px] text-brand-400">{visit.token_code}</span>
        </div>
        <p className="mt-0.5 truncate text-xs text-ink-400">
          {visit.patient.age}y · {visit.patient.gender} · {visit.chief_complaint || 'No complaint noted'}
        </p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        <PriorityBadge priority={visit.priority} />
        {trailing ?? (
          <span className="flex items-center gap-1 text-[11px] text-ink-500">
            <Clock size={11} />
            {formatMinutes(visit.predicted_wait_minutes ?? 0)}
          </span>
        )}
      </div>
    </motion.button>
  )
}

export function VisitCardCompactStatus({ visit }: { visit: Visit }) {
  return <StatusBadge status={visit.status} />
}

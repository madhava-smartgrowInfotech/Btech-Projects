import { type ReactNode, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ArrowRight, Droplet, Thermometer, Wind } from 'lucide-react'

import { PriorityBadge, StatusBadge } from '@/components/ui/Badge'
import { Button, type ButtonProps } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { getMovements } from '@/lib/api'
import { formatMinutes, formatTime } from '@/lib/utils'
import type { Visit } from '@/types'

export interface VisitAction {
  label: string
  icon?: ReactNode
  onClick: () => void
  variant?: ButtonProps['variant']
  disabled?: boolean
}

interface Movement {
  id: string
  from_department_id: string | null
  to_department_id: string | null
  note: string | null
  timestamp: string
}

export function VisitDetailModal({
  visit,
  open,
  onOpenChange,
  actions,
  departmentName,
}: {
  visit: Visit | null
  open: boolean
  onOpenChange: (open: boolean) => void
  actions: VisitAction[]
  departmentName: (id?: string | null) => string
}) {
  const [movements, setMovements] = useState<Movement[]>([])

  useEffect(() => {
    if (visit && open) getMovements(visit.id).then(setMovements)
  }, [visit?.id, open])

  if (!visit) return null

  const vitalItems = [
    { icon: Activity, label: 'Heart rate', value: visit.vitals?.heart_rate, unit: 'bpm' },
    { icon: Droplet, label: 'SpO2', value: visit.vitals?.spo2, unit: '%' },
    { icon: Thermometer, label: 'Temp', value: visit.vitals?.temperature_c, unit: '°C' },
    { icon: Wind, label: 'Resp. rate', value: visit.vitals?.respiratory_rate, unit: '/min' },
  ]

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={visit.patient.name}
      description={`${visit.patient.age}y · ${visit.patient.gender} · MRN ${visit.patient.mrn} · Token ${visit.token_code}`}
      maxWidth="max-w-xl"
    >
      <div className="flex flex-wrap items-center gap-2">
        <PriorityBadge priority={visit.priority} />
        <StatusBadge status={visit.status} />
        {visit.predicted_wait_minutes != null && (
          <span className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] text-ink-300">
            Predicted wait: {formatMinutes(visit.predicted_wait_minutes)}
          </span>
        )}
      </div>

      <div className="mt-4 rounded-xl border border-white/8 bg-ink-950/40 p-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
          Chief complaint
        </p>
        <p className="text-sm text-ink-200">{visit.chief_complaint || '—'}</p>
      </div>

      {visit.vitals && (
        <div className="mt-4 grid grid-cols-4 gap-3">
          {vitalItems.map((v) => (
            <div key={v.label} className="rounded-xl border border-white/8 bg-ink-950/40 p-3 text-center">
              <v.icon size={15} className="mx-auto text-brand-400" />
              <p className="mt-1.5 text-sm font-semibold text-white">
                {v.value ?? '—'}
                {v.value != null && <span className="text-[10px] text-ink-500"> {v.unit}</span>}
              </p>
              <p className="text-[10px] text-ink-500">{v.label}</p>
            </div>
          ))}
        </div>
      )}

      {movements.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500">
            Movement timeline
          </p>
          <div className="space-y-2">
            {movements.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-2 text-xs text-ink-400"
              >
                <span className="text-ink-600">{formatTime(m.timestamp)}</span>
                <span>{departmentName(m.from_department_id)}</span>
                <ArrowRight size={11} />
                <span className="font-medium text-ink-200">{departmentName(m.to_department_id)}</span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {actions.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2 border-t border-white/8 pt-5">
          {actions.map((a) => (
            <Button key={a.label} variant={a.variant} onClick={a.onClick} disabled={a.disabled} size="sm">
              {a.icon}
              {a.label}
            </Button>
          ))}
        </div>
      )}
    </Modal>
  )
}

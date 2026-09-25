import { useEffect, useState } from 'react'
import { BedDouble } from 'lucide-react'

import { Modal } from '@/components/ui/Modal'
import { listBeds } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { Bed, Department } from '@/types'

export function AdmitModal({
  open,
  onOpenChange,
  wardDepartments,
  onAdmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  wardDepartments: Department[]
  onAdmit: (bedId: string) => Promise<void>
}) {
  const [activeDept, setActiveDept] = useState<string>('')
  const [beds, setBeds] = useState<Bed[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open && wardDepartments.length && !activeDept) setActiveDept(wardDepartments[0].id)
  }, [open, wardDepartments, activeDept])

  useEffect(() => {
    if (open && activeDept) listBeds(activeDept).then(setBeds)
  }, [open, activeDept])

  async function handleAdmit(bedId: string) {
    setLoading(true)
    try {
      await onAdmit(bedId)
      onOpenChange(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Admit patient" description="Pick a ward or ICU bed" maxWidth="max-w-lg">
      <div className="mb-4 flex gap-2">
        {wardDepartments.map((d) => (
          <button
            key={d.id}
            onClick={() => setActiveDept(d.id)}
            className={cn(
              'rounded-lg px-3 py-1.5 text-xs font-medium transition-colors',
              activeDept === d.id ? 'bg-brand-500 text-white' : 'bg-ink-900 text-ink-400 hover:text-white',
            )}
          >
            {d.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-4 gap-2.5">
        {beds.map((bed) => (
          <button
            key={bed.id}
            disabled={bed.status !== 'available' || loading}
            onClick={() => handleAdmit(bed.id)}
            className={cn(
              'flex flex-col items-center gap-1.5 rounded-xl border p-3 text-xs transition-colors',
              bed.status === 'available'
                ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300 hover:bg-emerald-500/15'
                : bed.status === 'cleaning'
                  ? 'border-amber-500/20 bg-amber-500/5 text-amber-400/70 cursor-not-allowed'
                  : 'border-white/8 bg-white/[0.02] text-ink-600 cursor-not-allowed',
            )}
          >
            <BedDouble size={18} />
            <span className="font-semibold">{bed.bed_number}</span>
            <span className="capitalize">{bed.status}</span>
          </button>
        ))}
        {beds.length === 0 && (
          <p className="col-span-4 py-6 text-center text-sm text-ink-500">No beds configured.</p>
        )}
      </div>
    </Modal>
  )
}

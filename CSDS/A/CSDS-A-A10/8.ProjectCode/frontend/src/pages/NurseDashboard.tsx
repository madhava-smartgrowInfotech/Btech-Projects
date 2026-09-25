import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { BedDouble, LogOut as DischargeIcon, Sparkles } from 'lucide-react'

import { AppShell } from '@/components/layout/AppShell'
import { VisitDetailModal, type VisitAction } from '@/components/dashboard/VisitDetailModal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import { getDepartments, listBeds, listVisits, releaseBed, updateBedStatus } from '@/lib/api'
import { cn } from '@/lib/utils'
import { toast } from '@/store/toast'
import type { Bed, Department, Visit } from '@/types'

export default function NurseDashboard() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [beds, setBeds] = useState<Bed[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [selected, setSelected] = useState<Visit | null>(null)

  async function refresh() {
    const depts = await getDepartments()
    const wardDepts = depts.filter((d) => ['ward', 'icu'].includes(d.type))
    setDepartments(depts)
    const [bedLists, admittedVisits] = await Promise.all([
      Promise.all(wardDepts.map((d) => listBeds(d.id))),
      listVisits({ status_in: 'admitted_ward,admitted_icu' }),
    ])
    setBeds(bedLists.flat())
    setVisits(admittedVisits)
  }

  useEffect(() => {
    refresh()
  }, [])

  useLiveSocket((evt) => {
    if (['bed_updated', 'visit_updated', 'visit_created'].includes(evt.event)) refresh()
  })

  const visitByBed = useMemo(() => {
    const map: Record<string, Visit> = {}
    visits.forEach((v) => {
      if (v.bed_id) map[v.bed_id] = v
    })
    return map
  }, [visits])

  const departmentName = (id?: string | null) => departments.find((d) => d.id === id)?.name ?? 'Registration'
  const wardDepartments = departments.filter((d) => ['ward', 'icu'].includes(d.type))

  async function markAvailable(bed: Bed) {
    await updateBedStatus(bed.id, 'available')
    toast({ title: `Bed ${bed.bed_number} marked available`, variant: 'success' })
    refresh()
  }

  function actionsFor(visit: Visit): VisitAction[] {
    return [
      {
        label: 'Discharge & Release Bed',
        icon: <DischargeIcon size={15} />,
        variant: 'danger',
        onClick: async () => {
          await releaseBed(visit.id)
          toast({ title: `${visit.patient.name} discharged, bed set to cleaning`, variant: 'success' })
          setSelected(null)
          refresh()
        },
      },
    ]
  }

  return (
    <AppShell title="Ward & ICU" subtitle="Live bed availability and admitted patients">
      <Tabs defaultValue={wardDepartments[0]?.id}>
        <TabsList>
          {wardDepartments.map((d) => (
            <TabsTrigger key={d.id} value={d.id}>
              {d.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {wardDepartments.map((dept) => {
          const deptBeds = beds.filter((b) => b.department_id === dept.id)
          const available = deptBeds.filter((b) => b.status === 'available').length
          return (
            <TabsContent key={dept.id} value={dept.id} className="mt-5">
              <Card>
                <CardHeader>
                  <CardTitle>{dept.name} Beds</CardTitle>
                  <span className="text-xs text-ink-500">
                    {available} / {deptBeds.length} available
                  </span>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
                  {deptBeds.map((bed) => {
                    const visit = visitByBed[bed.id]
                    return (
                      <motion.div
                        key={bed.id}
                        layout
                        className={cn(
                          'flex flex-col items-center gap-2 rounded-xl border p-4 text-center',
                          bed.status === 'available' && 'border-emerald-500/30 bg-emerald-500/5',
                          bed.status === 'occupied' && 'cursor-pointer border-rose-500/30 bg-rose-500/5 hover:bg-rose-500/10',
                          bed.status === 'cleaning' && 'cursor-pointer border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/10',
                        )}
                        onClick={() => {
                          if (bed.status === 'occupied' && visit) setSelected(visit)
                          if (bed.status === 'cleaning') markAvailable(bed)
                        }}
                      >
                        <BedDouble
                          size={20}
                          className={cn(
                            bed.status === 'available' && 'text-emerald-400',
                            bed.status === 'occupied' && 'text-rose-400',
                            bed.status === 'cleaning' && 'text-amber-400',
                          )}
                        />
                        <p className="text-sm font-semibold text-white">{bed.bed_number}</p>
                        {visit ? (
                          <p className="truncate text-[11px] text-ink-400">{visit.patient.name}</p>
                        ) : (
                          <p className="text-[11px] capitalize text-ink-500">
                            {bed.status === 'cleaning' ? 'Tap to clear' : bed.status}
                          </p>
                        )}
                      </motion.div>
                    )
                  })}
                </CardContent>
              </Card>
            </TabsContent>
          )
        })}
      </Tabs>

      <div className="mt-3 flex items-center gap-1.5 text-xs text-ink-500">
        <Sparkles size={12} />
        Tap an occupied bed for patient details, or a cleaning bed to mark it available.
      </div>

      <VisitDetailModal
        visit={selected}
        open={!!selected}
        onOpenChange={(o) => !o && setSelected(null)}
        actions={selected ? actionsFor(selected) : []}
        departmentName={departmentName}
      />
    </AppShell>
  )
}

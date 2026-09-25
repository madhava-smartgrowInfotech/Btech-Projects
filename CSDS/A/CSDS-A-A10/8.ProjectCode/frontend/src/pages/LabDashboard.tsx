import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, Clock, FlaskConical, PlayCircle } from 'lucide-react'

import { AppShell } from '@/components/layout/AppShell'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import { listLabTests, listVisits, updateLabTestStatus } from '@/lib/api'
import { formatTime } from '@/lib/utils'
import { toast } from '@/store/toast'
import type { LabTest, LabTestStatus, Visit } from '@/types'

const COLUMNS: { status: LabTestStatus; label: string; next?: LabTestStatus; nextLabel?: string }[] = [
  { status: 'ordered', label: 'Ordered', next: 'scheduled', nextLabel: 'Schedule' },
  { status: 'scheduled', label: 'Scheduled', next: 'in_progress', nextLabel: 'Start' },
  { status: 'in_progress', label: 'In Progress', next: 'completed', nextLabel: 'Complete' },
  { status: 'completed', label: 'Completed' },
]

export default function LabDashboard() {
  const [tests, setTests] = useState<LabTest[]>([])
  const [visits, setVisits] = useState<Visit[]>([])

  async function refresh() {
    const [labTests, allVisits] = await Promise.all([listLabTests(), listVisits()])
    setTests(labTests)
    setVisits(allVisits)
  }

  useEffect(() => {
    refresh()
  }, [])

  useLiveSocket((evt) => {
    if (['lab_test_created', 'lab_test_updated'].includes(evt.event)) refresh()
  })

  const visitMap = useMemo(() => {
    const map: Record<string, Visit> = {}
    visits.forEach((v) => (map[v.id] = v))
    return map
  }, [visits])

  async function advance(test: LabTest, next: LabTestStatus) {
    await updateLabTestStatus(test.id, next)
    toast({ title: `${test.test_name} marked ${next.replace('_', ' ')}`, variant: 'success' })
    refresh()
  }

  return (
    <AppShell title="Laboratory" subtitle="Order queue, scheduling and results">
      <div className="grid gap-5 lg:grid-cols-4">
        {COLUMNS.map((col) => {
          const items = tests
            .filter((t) => t.status === col.status)
            .slice(0, col.status === 'completed' ? 10 : undefined)
          return (
            <Card key={col.status}>
              <CardHeader>
                <CardTitle>{col.label}</CardTitle>
                <span className="text-xs text-ink-500">{items.length}</span>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <AnimatePresence initial={false}>
                  {items.map((test) => {
                    const visit = visitMap[test.visit_id]
                    return (
                      <motion.div
                        key={test.id}
                        layout
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        className="rounded-xl border border-white/8 bg-ink-850/60 p-3.5"
                      >
                        <div className="flex items-center gap-2.5">
                          {visit && <Avatar name={visit.patient.name} size={28} />}
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium text-white">
                              {visit?.patient.name ?? 'Unknown patient'}
                            </p>
                            <p className="flex items-center gap-1 text-[11px] text-ink-500">
                              <FlaskConical size={10} />
                              {test.test_name}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2.5 flex items-center justify-between">
                          <span className="flex items-center gap-1 text-[10px] text-ink-500">
                            <Clock size={10} />
                            {formatTime(test.ordered_at)}
                          </span>
                          {col.next && (
                            <Button size="sm" variant="secondary" onClick={() => advance(test, col.next!)}>
                              {col.status === 'in_progress' ? <CheckCircle2 size={13} /> : <PlayCircle size={13} />}
                              {col.nextLabel}
                            </Button>
                          )}
                        </div>
                      </motion.div>
                    )
                  })}
                </AnimatePresence>
                {items.length === 0 && (
                  <p className="py-8 text-center text-xs text-ink-500">Nothing here.</p>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </AppShell>
  )
}

import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence } from 'framer-motion'
import { BedDouble, FlaskConical, LogOut as DischargeIcon, PlayCircle } from 'lucide-react'

import { AppShell } from '@/components/layout/AppShell'
import { AdmitModal } from '@/components/dashboard/AdmitModal'
import { OrderLabModal } from '@/components/dashboard/OrderLabModal'
import { VisitCard } from '@/components/dashboard/VisitCard'
import { VisitDetailModal, type VisitAction } from '@/components/dashboard/VisitDetailModal'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import {
  admitToBed,
  assignDoctor,
  getDepartments,
  listVisits,
  orderLabTest,
  updateVisitStatus,
} from '@/lib/api'
import { useAuth } from '@/store/auth'
import { toast } from '@/store/toast'
import type { Department, Visit } from '@/types'

export default function DoctorDashboard() {
  const user = useAuth((s) => s.user)!
  const [departments, setDepartments] = useState<Department[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [selected, setSelected] = useState<Visit | null>(null)
  const [labOpen, setLabOpen] = useState(false)
  const [admitOpen, setAdmitOpen] = useState(false)

  async function refresh() {
    const [depts, myDeptVisits] = await Promise.all([
      getDepartments(),
      listVisits({
        department_id: user.department_id ?? undefined,
        status_in: 'waiting,in_consultation,lab_pending,lab_in_progress,pharmacy',
      }),
    ])
    setDepartments(depts)
    setVisits(myDeptVisits)
  }

  useEffect(() => {
    refresh()
  }, [])

  useLiveSocket((evt) => {
    if (['visit_created', 'visit_updated', 'lab_test_updated'].includes(evt.event)) refresh()
  })

  useEffect(() => {
    if (selected) {
      const fresh = visits.find((v) => v.id === selected.id)
      if (fresh) setSelected(fresh)
    }
  }, [visits]) // eslint-disable-line react-hooks/exhaustive-deps

  const waiting = useMemo(
    () => visits.filter((v) => v.status === 'waiting').sort((a, b) => a.token_number - b.token_number),
    [visits],
  )
  const myActive = useMemo(
    () => visits.filter((v) => v.assigned_doctor_id === user.id && ['in_consultation', 'lab_pending', 'lab_in_progress', 'pharmacy'].includes(v.status)),
    [visits, user.id],
  )
  const wardDepartments = departments.filter((d) => ['ward', 'icu'].includes(d.type))

  const departmentName = (id?: string | null) => departments.find((d) => d.id === id)?.name ?? 'Registration'

  async function callNext(visit: Visit) {
    await assignDoctor(visit.id, user.id)
    toast({ title: `${visit.patient.name} is now in consultation`, variant: 'success' })
    refresh()
  }

  function buildActions(visit: Visit): VisitAction[] {
    const actions: VisitAction[] = []
    if (visit.status === 'waiting') {
      actions.push({
        label: 'Start Consultation',
        icon: <PlayCircle size={15} />,
        onClick: () => callNext(visit).then(() => setSelected(null)),
      })
      return actions
    }
    actions.push({
      label: 'Order Lab Test',
      icon: <FlaskConical size={15} />,
      variant: 'secondary',
      onClick: () => setLabOpen(true),
    })
    actions.push({
      label: 'Admit',
      icon: <BedDouble size={15} />,
      variant: 'secondary',
      onClick: () => setAdmitOpen(true),
    })
    actions.push({
      label: 'Discharge',
      icon: <DischargeIcon size={15} />,
      variant: 'danger',
      onClick: async () => {
        await updateVisitStatus(visit.id, { status: 'discharged' })
        toast({ title: `${visit.patient.name} discharged`, variant: 'success' })
        setSelected(null)
        refresh()
      },
    })
    return actions
  }

  return (
    <AppShell title={`Welcome, ${user.name.split(' ')[0]}`} subtitle={`${user.specialty} · Live queue`}>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Waiting Queue</CardTitle>
            <span className="text-xs text-ink-500">{waiting.length} patients</span>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <AnimatePresence initial={false}>
              {waiting.map((v) => (
                <VisitCard key={v.id} visit={v} onClick={() => setSelected(v)} />
              ))}
            </AnimatePresence>
            {waiting.length === 0 && <p className="py-8 text-center text-sm text-ink-500">Queue is clear.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>My Active Patients</CardTitle>
            <span className="text-xs text-ink-500">{myActive.length} in progress</span>
          </CardHeader>
          <CardContent className="space-y-2.5">
            <AnimatePresence initial={false}>
              {myActive.map((v) => (
                <VisitCard key={v.id} visit={v} onClick={() => setSelected(v)} />
              ))}
            </AnimatePresence>
            {myActive.length === 0 && (
              <p className="py-8 text-center text-sm text-ink-500">No active consultations.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <VisitDetailModal
        visit={selected}
        open={!!selected}
        onOpenChange={(o) => !o && setSelected(null)}
        actions={selected ? buildActions(selected) : []}
        departmentName={departmentName}
      />

      <OrderLabModal
        open={labOpen}
        onOpenChange={setLabOpen}
        onSubmit={async (testName) => {
          if (!selected) return
          await orderLabTest(selected.id, testName)
          toast({ title: `${testName} ordered for ${selected.patient.name}`, variant: 'success' })
          refresh()
        }}
      />

      <AdmitModal
        open={admitOpen}
        onOpenChange={setAdmitOpen}
        wardDepartments={wardDepartments}
        onAdmit={async (bedId) => {
          if (!selected) return
          await admitToBed(selected.id, bedId)
          toast({ title: `${selected.patient.name} admitted`, variant: 'success' })
          setSelected(null)
          refresh()
        }}
      />
    </AppShell>
  )
}

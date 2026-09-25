import { type FormEvent, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { HeartPulse, Loader2, Plus, Sparkles, UserPlus } from 'lucide-react'

import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Input, Label, NativeSelect, Textarea } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { PriorityBadge, StatusBadge } from '@/components/ui/Badge'
import { createVisit, getDepartments, listVisits } from '@/lib/api'
import { formatMinutes, formatTime } from '@/lib/utils'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import { toast } from '@/store/toast'
import type { Department, Visit } from '@/types'

const emptyForm = {
  name: '',
  age: '',
  gender: 'Male',
  phone: '',
  blood_group: '',
  department_id: '',
  chief_complaint: '',
  heart_rate: '',
  systolic_bp: '',
  spo2: '',
  temperature_c: '',
  respiratory_rate: '',
}

export default function ReceptionDashboard() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [visits, setVisits] = useState<Visit[]>([])
  const [open, setOpen] = useState(false)
  const [showVitals, setShowVitals] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [lastPredicted, setLastPredicted] = useState<Visit | null>(null)

  async function refresh() {
    const [depts, v] = await Promise.all([getDepartments(), listVisits()])
    setDepartments(depts)
    setVisits(v.slice(0, 40))
  }

  useEffect(() => {
    refresh()
  }, [])

  useLiveSocket((evt) => {
    if (['visit_created', 'visit_updated'].includes(evt.event)) refresh()
  })

  function update<K extends keyof typeof emptyForm>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      const visit = await createVisit({
        patient: {
          name: form.name,
          age: Number(form.age),
          gender: form.gender,
          phone: form.phone || undefined,
          blood_group: form.blood_group || undefined,
        },
        department_id: form.department_id,
        chief_complaint: form.chief_complaint,
        vitals: showVitals
          ? {
              heart_rate: form.heart_rate ? Number(form.heart_rate) : undefined,
              systolic_bp: form.systolic_bp ? Number(form.systolic_bp) : undefined,
              spo2: form.spo2 ? Number(form.spo2) : undefined,
              temperature_c: form.temperature_c ? Number(form.temperature_c) : undefined,
              respiratory_rate: form.respiratory_rate ? Number(form.respiratory_rate) : undefined,
            }
          : undefined,
      })
      setLastPredicted(visit)
      toast({
        title: `Token ${visit.token_code} generated`,
        description: `${visit.patient.name} · priority: ${visit.priority}`,
        variant: 'success',
      })
      setForm(emptyForm)
      setShowVitals(false)
      setOpen(false)
      refresh()
    } catch {
      toast({ title: 'Could not register patient', variant: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AppShell
      title="Reception"
      subtitle="Register walk-ins and issue digital tokens"
      actions={
        <Button onClick={() => setOpen(true)}>
          <Plus size={17} />
          New Registration
        </Button>
      }
    >
      {lastPredicted && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex flex-wrap items-center gap-4 rounded-2xl border border-brand-500/20 bg-brand-500/5 p-4"
        >
          <Sparkles size={18} className="text-brand-400" />
          <p className="text-sm text-ink-200">
            <span className="font-semibold text-white">{lastPredicted.patient.name}</span> issued token{' '}
            <span className="font-mono font-semibold text-brand-300">{lastPredicted.token_code}</span>
          </p>
          <PriorityBadge priority={lastPredicted.priority} />
          <span className="text-sm text-ink-400">
            Predicted wait: {formatMinutes(lastPredicted.predicted_wait_minutes ?? 0)}
          </span>
        </motion.div>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/8 text-left text-xs uppercase tracking-wide text-ink-500">
                <th className="px-5 py-3 font-medium">Token</th>
                <th className="px-5 py-3 font-medium">Patient</th>
                <th className="px-5 py-3 font-medium">Complaint</th>
                <th className="px-5 py-3 font-medium">Priority</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Registered</th>
              </tr>
            </thead>
            <tbody>
              {visits.map((v) => (
                <motion.tr
                  key={v.id}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="border-b border-white/5 last:border-0 hover:bg-white/[0.02]"
                >
                  <td className="px-5 py-3 font-mono text-brand-300">{v.token_code}</td>
                  <td className="px-5 py-3">
                    <p className="font-medium text-white">{v.patient.name}</p>
                    <p className="text-xs text-ink-500">
                      {v.patient.age}y · {v.patient.gender} · {v.patient.mrn}
                    </p>
                  </td>
                  <td className="max-w-[220px] truncate px-5 py-3 text-ink-300">{v.chief_complaint}</td>
                  <td className="px-5 py-3">
                    <PriorityBadge priority={v.priority} />
                  </td>
                  <td className="px-5 py-3">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="px-5 py-3 text-ink-400">{formatTime(v.created_at)}</td>
                </motion.tr>
              ))}
              {visits.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-ink-500">
                    No registrations yet today.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Register new patient"
        description="Generates a digital token and an AI-predicted wait time instantly."
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Full name</Label>
              <Input required value={form.name} onChange={(e) => update('name', e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Age</Label>
                <Input required type="number" min={0} max={130} value={form.age} onChange={(e) => update('age', e.target.value)} />
              </div>
              <div>
                <Label>Gender</Label>
                <NativeSelect value={form.gender} onChange={(e) => update('gender', e.target.value)}>
                  <option>Male</option>
                  <option>Female</option>
                  <option>Other</option>
                </NativeSelect>
              </div>
            </div>
            <div>
              <Label>Phone</Label>
              <Input value={form.phone} onChange={(e) => update('phone', e.target.value)} placeholder="Optional" />
            </div>
            <div>
              <Label>Blood group</Label>
              <Input value={form.blood_group} onChange={(e) => update('blood_group', e.target.value)} placeholder="e.g. O+" />
            </div>
          </div>

          <div>
            <Label>Department</Label>
            <NativeSelect
              required
              value={form.department_id}
              onChange={(e) => update('department_id', e.target.value)}
            >
              <option value="">Select department</option>
              {departments
                .filter((d) => !['ward', 'icu'].includes(d.type))
                .map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
            </NativeSelect>
          </div>

          <div>
            <Label>Chief complaint</Label>
            <Textarea
              required
              rows={2}
              value={form.chief_complaint}
              onChange={(e) => update('chief_complaint', e.target.value)}
              placeholder="Reason for visit"
            />
          </div>

          <div>
            <button
              type="button"
              onClick={() => setShowVitals((s) => !s)}
              className="flex items-center gap-1.5 text-xs font-medium text-brand-400 hover:text-brand-300"
            >
              <HeartPulse size={14} />
              {showVitals ? 'Hide vitals' : 'Add vitals for triage scoring'}
            </button>

            {showVitals && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 grid grid-cols-3 gap-3 rounded-xl border border-white/8 bg-ink-950/40 p-4"
              >
                <div>
                  <Label>Heart rate (bpm)</Label>
                  <Input type="number" value={form.heart_rate} onChange={(e) => update('heart_rate', e.target.value)} />
                </div>
                <div>
                  <Label>Systolic BP</Label>
                  <Input type="number" value={form.systolic_bp} onChange={(e) => update('systolic_bp', e.target.value)} />
                </div>
                <div>
                  <Label>SpO2 (%)</Label>
                  <Input type="number" value={form.spo2} onChange={(e) => update('spo2', e.target.value)} />
                </div>
                <div>
                  <Label>Temperature (°C)</Label>
                  <Input type="number" step="0.1" value={form.temperature_c} onChange={(e) => update('temperature_c', e.target.value)} />
                </div>
                <div>
                  <Label>Respiratory rate</Label>
                  <Input type="number" value={form.respiratory_rate} onChange={(e) => update('respiratory_rate', e.target.value)} />
                </div>
              </motion.div>
            )}
          </div>

          <Button type="submit" size="lg" disabled={submitting} className="w-full">
            {submitting ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
            {submitting ? 'Generating token…' : 'Register & generate token'}
          </Button>
        </form>
      </Modal>
    </AppShell>
  )
}

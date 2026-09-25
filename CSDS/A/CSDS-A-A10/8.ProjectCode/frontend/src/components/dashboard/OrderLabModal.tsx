import { type FormEvent, useState } from 'react'
import { FlaskConical } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import { Input, Label } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'

const COMMON_TESTS = ['Complete Blood Count', 'Blood Glucose', 'Lipid Profile', 'X-Ray Chest', 'ECG', 'Urinalysis']

export function OrderLabModal({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (testName: string) => Promise<void>
}) {
  const [testName, setTestName] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!testName.trim()) return
    setSubmitting(true)
    try {
      await onSubmit(testName.trim())
      setTestName('')
      onOpenChange(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Order lab test" maxWidth="max-w-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Test name</Label>
          <Input value={testName} onChange={(e) => setTestName(e.target.value)} placeholder="e.g. Complete Blood Count" required />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {COMMON_TESTS.map((t) => (
            <button
              type="button"
              key={t}
              onClick={() => setTestName(t)}
              className="rounded-full border border-white/10 px-2.5 py-1 text-[11px] text-ink-300 hover:border-brand-400/40 hover:text-brand-300"
            >
              {t}
            </button>
          ))}
        </div>
        <Button type="submit" className="w-full" disabled={submitting}>
          <FlaskConical size={16} />
          {submitting ? 'Ordering…' : 'Order test'}
        </Button>
      </form>
    </Modal>
  )
}

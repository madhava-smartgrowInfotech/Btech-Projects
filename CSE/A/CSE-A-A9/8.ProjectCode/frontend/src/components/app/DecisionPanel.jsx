import { useState } from 'react'
import { Check, Lock, X } from 'lucide-react'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { Button, Modal, Textarea, useToast } from '../ui'
import { Callout, StatusBadge } from './index'

const COPY = {
  confirm: { title: 'Confirm as fake', verb: 'Confirmed', variant: 'danger', icon: Check, help: 'The account counts as fake in the next training run.' },
  dismiss: { title: 'Dismiss as genuine', verb: 'Dismissed', variant: 'mint', icon: X, help: 'The account counts as genuine in the next training run.' },
}

/** Confirm / dismiss buttons with an optional note. Analysts see why they cannot act. */
export function DecisionPanel({ targetType, targetId, status, members = 1, onDone }) {
  const { user } = useAuth()
  const toast = useToast()
  const [mode, setMode] = useState(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const thing = targetType === 'cluster' ? `cluster ${targetId} (${members} accounts)` : `account ${targetId}`

  const close = () => {
    setMode(null)
    setNote('')
    setError('')
  }
  const submit = async () => {
    setBusy(true)
    setError('')
    try {
      const r = await api.decide(targetType, targetId, mode, note)
      toast({ kind: 'success', title: `${COPY[mode].verb} ${targetType} ${targetId}`, message: `${r.affected_accounts} account${r.affected_accounts === 1 ? '' : 's'} logged for the next training run.` })
      close()
      onDone?.()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  if (user?.role !== 'moderator') {
    return (
      <Callout tone="info" title="Read-only access">
        <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
          <Lock size={14} aria-hidden="true" /> Analysts can explore everything. Sign in as the moderator demo account to record decisions.
        </span>
      </Callout>
    )
  }

  const c = mode ? COPY[mode] : null
  return (
    <div className="stack" style={{ '--gap': '12px' }}>
      <div className="row between">
        <span className="small muted">Current status</span>
        <StatusBadge status={status} />
      </div>
      <div className="decision-bar">
        <Button variant="danger" icon={Check} onClick={() => setMode('confirm')}>
          Confirm fake
        </Button>
        <Button variant="mint" icon={X} onClick={() => setMode('dismiss')}>
          Dismiss
        </Button>
      </div>
      <Modal
        open={!!mode}
        onClose={close}
        title={c ? `${c.title}?` : ''}
        description={c ? `You are about to mark ${thing}. ${c.help}` : ''}
        footer={
          <>
            <Button variant="ghost" onClick={close} disabled={busy}>
              Cancel
            </Button>
            <Button variant={c?.variant} icon={c?.icon} loading={busy} onClick={submit}>
              {c?.verb}
            </Button>
          </>
        }
      >
        <div className="stack" style={{ '--gap': '12px' }}>
          {error && (
            <Callout tone="error" title="Decision not saved">
              {error}
            </Callout>
          )}
          <Textarea id="decision-note" label="Note (optional)" rows={3} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Why? e.g. posts identical links every hour" data-autofocus />
        </div>
      </Modal>
    </div>
  )
}

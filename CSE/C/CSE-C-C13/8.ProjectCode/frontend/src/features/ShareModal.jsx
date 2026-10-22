import { useCallback, useEffect, useState } from 'react'
import { Trash2, UserPlus } from 'lucide-react'
import { api } from '../lib/api'
import { ROLE, when } from '../lib/format'
import { shareWith } from '../lib/vault'
import { Badge, Button, EmptyState, ErrorState, IconButton, Input, Modal, Select, Skeleton, useToast } from '../components/ui'
import { useVaultKey } from './UnlockGate'

const ROLE_OPTIONS = [
  { value: 'viewer', label: 'Viewer - read and download' },
  { value: 'editor', label: 'Editor - read, download, replace content' },
]

export default function ShareModal({ file, open, onClose, onChanged }) {
  const toast = useToast()
  const ensureKey = useVaultKey()
  const [perms, setPerms] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('viewer')
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirmUid, setConfirmUid] = useState(null)

  const load = useCallback(async () => {
    setLoadError(null)
    try {
      setPerms(await api.permissions(file.id))
    } catch (e) {
      setLoadError(e)
    }
  }, [file.id])

  useEffect(() => {
    if (open) {
      setPerms(null)
      setFormError('')
      setConfirmUid(null)
      load()
    }
  }, [open, load])

  const grant = async (e) => {
    e.preventDefault()
    setFormError('')
    if (!email.trim()) {
      setFormError('Enter the recipient email address.')
      return
    }
    setBusy(true)
    try {
      const key = await ensureKey()
      const target = await shareWith(file.id, email, role, key)
      toast({ title: 'Access granted', message: `${target.email} can now open this file as ${role}.` })
      setEmail('')
      await load()
      onChanged?.()
    } catch (err) {
      setFormError(err.status === 409 ? 'That user already has access. Change their role below instead.' : err.message)
    } finally {
      setBusy(false)
    }
  }

  const changeRole = async (uid, next) => {
    try {
      await api.changeRole(file.id, uid, next)
      toast({ title: 'Role updated', message: `Now ${next}.` })
      await load()
      onChanged?.()
    } catch (err) {
      toast({ tone: 'error', title: 'Could not change role', message: err.message })
    }
  }

  const revoke = async (uid) => {
    try {
      await api.revoke(file.id, uid)
      toast({ title: 'Access revoked' })
      setConfirmUid(null)
      await load()
      onChanged?.()
    } catch (err) {
      toast({ tone: 'error', title: 'Could not revoke access', message: err.message })
    }
  }

  const others = (perms || []).filter((p) => p.role !== 'owner')

  return (
    <Modal open={open} onClose={onClose} title={`Share “${file.original_filename}”`} footer={<Button onClick={onClose}>Done</Button>}>
      <form onSubmit={grant} className="stack" noValidate>
        <Input
          label="Recipient email"
          type="email"
          placeholder="colleague@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          hint="They must already have a CipherVault account."
          error={formError}
          data-autofocus
        />
        <Select label="Role" value={role} onChange={(e) => setRole(e.target.value)} options={ROLE_OPTIONS} />
        <Button variant="primary" type="submit" icon={UserPlus} loading={busy}>
          Grant access
        </Button>
        <p className="faint">The file key is unwrapped and re-wrapped for the recipient in this browser. It is never sent in plaintext.</p>
      </form>

      <h3 style={{ fontSize: 15, margin: '24px 0 4px' }}>Who has access</h3>
      {loadError ? (
        <ErrorState title="Could not load access list" error={loadError} onRetry={load} />
      ) : !perms ? (
        <div aria-busy="true">
          <Skeleton height={20} style={{ margin: '14px 0' }} />
          <Skeleton height={20} style={{ margin: '14px 0' }} />
        </div>
      ) : (
        <>
          {perms
            .filter((p) => p.role === 'owner')
            .map((p) => (
              <div className="access-row" key={p.user_id}>
                <div style={{ minWidth: 0 }}>
                  <strong className="break">{p.user_email}</strong>
                  <div className="faint">{p.user_name}</div>
                </div>
                <Badge tone={ROLE.owner.tone}>Owner</Badge>
              </div>
            ))}
          {!others.length && (
            <EmptyState title="Not shared yet">Only you can open this file. Grant access above to collaborate.</EmptyState>
          )}
          {others.map((p) => (
            <div className="access-row" key={p.user_id}>
              <div style={{ minWidth: 0 }}>
                <strong className="break">{p.user_email}</strong>
                <div className="faint">Added {when(p.created_at)}</div>
              </div>
              <div className="row">
                <Select
                  labelHidden
                  label={`Role for ${p.user_email}`}
                  value={p.role}
                  onChange={(e) => changeRole(p.user_id, e.target.value)}
                  options={[
                    { value: 'viewer', label: 'Viewer' },
                    { value: 'editor', label: 'Editor' },
                  ]}
                />
                {confirmUid === p.user_id ? (
                  <>
                    <Button size="sm" variant="danger" onClick={() => revoke(p.user_id)}>
                      Confirm revoke
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setConfirmUid(null)}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <IconButton icon={Trash2} label={`Revoke access for ${p.user_email}`} onClick={() => setConfirmUid(p.user_id)} />
                )}
              </div>
            </div>
          ))}
        </>
      )}
    </Modal>
  )
}

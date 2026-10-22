import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { KeyRound } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { Button, Input, Modal, useToast } from '../components/ui'

const Ctx = createContext(async () => null)

// Resolves to the decrypted private key, asking for the password first when the vault is locked.
export const useVaultKey = () => useContext(Ctx)

export default function UnlockGate({ children }) {
  const { unlocked, privateKey, unlock, user } = useAuth()
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const waiting = useRef([])
  const keyRef = useRef(privateKey)
  keyRef.current = privateKey

  // After a page reload the key is gone - ask once on arrival, but let the user dismiss and browse metadata.
  // (A deliberate "Lock vault now" does not re-open the dialog; the next action that needs the key does.)
  useEffect(() => {
    if (!unlocked) setOpen(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const ensure = useCallback(() => {
    if (keyRef.current) return Promise.resolve(keyRef.current)
    setOpen(true)
    return new Promise((resolve, reject) => waiting.current.push({ resolve, reject }))
  }, [])

  const close = () => {
    setOpen(false)
    setPw('')
    setErr('')
    waiting.current.splice(0).forEach((w) => w.reject(new Error('Vault is locked. Enter your password to continue.')))
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setErr('')
    try {
      const key = await unlock(pw)
      setOpen(false)
      setPw('')
      waiting.current.splice(0).forEach((w) => w.resolve(key))
      toast({ title: 'Vault unlocked', message: 'Your private key is decrypted in this tab only.' })
    } catch (ex) {
      setErr(ex.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Ctx.Provider value={ensure}>
      {children}
      <Modal
        open={open && !unlocked}
        onClose={close}
        title="Unlock your vault"
        footer={
          <>
            <Button variant="ghost" onClick={close}>
              Not now
            </Button>
            <Button variant="primary" type="submit" form="unlock-form" loading={busy} disabled={!pw} icon={KeyRound}>
              Unlock
            </Button>
          </>
        }
      >
        <form id="unlock-form" onSubmit={submit} className="stack">
          <p className="muted">
            Your private key is stored encrypted. Enter the password for <strong>{user?.email}</strong> to decrypt it locally. It never leaves your browser in
            plaintext, and a page reload locks it again.
          </p>
          <Input
            data-autofocus
            label="Password"
            type="password"
            autoComplete="current-password"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            error={err}
          />
        </form>
      </Modal>
    </Ctx.Provider>
  )
}

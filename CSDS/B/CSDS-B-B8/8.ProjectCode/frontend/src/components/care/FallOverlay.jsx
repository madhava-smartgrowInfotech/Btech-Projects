import { useEffect, useRef, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { api } from '../../lib/api'
import { useMonitor } from '../../lib/monitor'
import { Button } from '../ui/controls'
import { Modal, useToast } from '../ui/feedback'

// Global "I'm OK" countdown. Shown on every signed-in screen while a fall alert is pending.
// It cannot be dismissed with Escape or a click outside: only "I'm OK" cancels the alert.
export default function FallOverlay() {
  const { state, refresh } = useMonitor()
  const toast = useToast()
  const pending = state?.alert || null
  const [shown, setShown] = useState(null)
  const [left, setLeft] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const lastId = useRef(null)

  // adopt the server's value on each poll, count down locally in between
  useEffect(() => {
    if (!pending) return
    setShown(pending)
    setLeft(pending.seconds_left)
    lastId.current = pending.id
  }, [pending?.id, pending?.seconds_left]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!shown) return undefined
    const t = setInterval(() => setLeft((l) => Math.max(0, l - 0.2)), 200)
    return () => clearInterval(t)
  }, [shown])

  // the alert left the "pending" state without us pressing the button: report what happened
  useEffect(() => {
    if (pending || !lastId.current) return
    const id = lastId.current
    lastId.current = null
    setShown(null)
    api
      .get('/alerts', { params: { limit: 10 } })
      .then((list) => {
        const a = list.find((x) => x.id === id)
        if (!a || a.status === 'cancelled') return
        if (a.status === 'sent') toast({ title: `Alert #${id} was sent`, message: 'Your contacts have been notified.', tone: 'error' })
        else toast({ title: `Alert #${id}: ${a.status}`, message: 'Open Alerts for the delivery details.', tone: 'info' })
      })
      .catch(() => {})
  }, [pending, toast])

  const ok = async () => {
    if (!shown) return
    setBusy(true)
    setError('')
    try {
      await api.post(`/alerts/${shown.id}/ok`)
      lastId.current = null
      setShown(null)
      toast({ title: "Alert cancelled", message: "Thanks - glad you're OK." })
      refresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal open={!!shown} onClose={() => {}} dismissable={false} title="Possible fall detected">
      <div className="fall-overlay">
        <span className="fall-icon" aria-hidden="true">
          <AlertTriangle size={34} />
        </span>
        <p className="muted">Emergency alerts go to your contacts in</p>
        <div className="fall-count" role="timer" aria-live="off">
          {Math.ceil(left)}
        </div>
        <span className="sr-only" role="status" aria-live="assertive">
          {Math.ceil(left) % 5 === 0 ? `${Math.ceil(left)} seconds left to cancel the alert` : ''}
        </span>
        <Button variant="primary" size="lg" className="fall-ok" loading={busy} onClick={ok} data-autofocus>
          I&apos;m OK
        </Button>
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </Modal>
  )
}

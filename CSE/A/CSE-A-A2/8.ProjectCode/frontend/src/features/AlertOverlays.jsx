import { useState } from 'react'
import { Check, Copy, MapPinned, Send, TriangleAlert } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button, KeyValueList, Modal, ProgressBar, useToast } from '../components/ui'
import { COUNTDOWN_SECONDS, useMonitor } from '../state/MonitorContext'

/** Global overlays: the 15 s confirmation countdown and the "alert dispatched" summary. */
export function AlertOverlays() {
  const m = useMonitor()
  const nav = useNavigate()
  const toast = useToast()
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(m.dispatch.message)
      setCopied(true)
      toast.success('Dispatch message copied.')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Copy is blocked in this browser. Select the text and copy it manually.')
    }
  }

  return (
    <>
      <Modal
        open={Boolean(m.pending)}
        onClose={m.cancelAlert}
        dismissOnBackdrop={false}
        title="Possible accident detected"
        describedBy="countdown-desc"
        footer={
          <>
            <Button variant="primary" icon={Check} onClick={m.cancelAlert} data-autofocus>
              I'm fine, cancel
            </Button>
            <Button variant="danger" icon={Send} onClick={m.sendAlert}>
              Send alert now
            </Button>
          </>
        }
      >
        <div className="stack" id="countdown-desc">
          <p>
            ResQAI detected a <strong>{m.pending?.severity_label}</strong> impact ({Math.round((m.pending?.confidence ?? 0) * 100)}% accident probability). If you do not respond, an
            emergency alert with your location is sent automatically.
          </p>
          <div className="row-between" style={{ alignItems: 'flex-end' }}>
            <span className="display-xl" style={{ lineHeight: 0.8 }} aria-hidden="true">
              {Math.max(m.countdown, 0)}
            </span>
            <span className="mono small muted">seconds left</span>
          </div>
          <ProgressBar value={Math.max(m.countdown, 0)} max={COUNTDOWN_SECONDS} label="Time before the alert is sent" tone="coral" />
          <span className="sr-only" role="status" aria-live="polite">
            Alert will be sent in {Math.ceil(Math.max(m.countdown, 0) / 5) * 5} seconds unless you cancel.
          </span>
          <p className="tiny muted">Pressing Escape counts as a response and cancels the alert.</p>
        </div>
      </Modal>

      <Modal
        open={m.dispatchOpen && Boolean(m.dispatch)}
        onClose={() => m.setDispatchOpen(false)}
        title="Emergency alert dispatched"
        footer={
          <>
            <Button icon={copied ? Check : Copy} onClick={copy}>
              {copied ? 'Copied' : 'Copy message'}
            </Button>
            <Button
              icon={MapPinned}
              onClick={() => {
                m.setDispatchOpen(false)
                nav('/response')
              }}
            >
              View on map
            </Button>
            <Button variant="primary" onClick={() => m.setDispatchOpen(false)}>
              Close
            </Button>
          </>
        }
      >
        {m.dispatch && (
          <div className="stack">
            <KeyValueList
              items={[
                { label: 'Alert ID', value: m.dispatch.alert_id },
                { label: 'Severity', value: m.dispatch.severity_label },
                { label: 'Location', value: `${m.dispatch.location.lat.toFixed(5)}, ${m.dispatch.location.lon.toFixed(5)} (${m.dispatch.located ? 'device GPS' : 'default area'})` },
                { label: 'Ambulance', value: m.dispatch.ambulance_number },
                { label: 'Emergency', value: m.dispatch.national_emergency_number },
              ]}
            />
            <pre className="mono small" style={{ whiteSpace: 'pre-wrap', margin: 0, padding: 12, border: 'var(--bw) solid var(--line)', background: 'var(--surface-2)', overflowWrap: 'anywhere' }}>
              {m.dispatch.message}
            </pre>
            <p className="tiny muted row" style={{ '--gap': '6px' }}>
              <TriangleAlert size={14} aria-hidden="true" /> Demo build: the message is drafted but not sent to real responders.
            </p>
          </div>
        )}
      </Modal>
    </>
  )
}

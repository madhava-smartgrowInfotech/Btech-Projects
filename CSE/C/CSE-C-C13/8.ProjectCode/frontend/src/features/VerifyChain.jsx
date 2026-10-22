import { useState } from 'react'
import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { api } from '../lib/api'
import { Button, useToast } from '../components/ui'

// Runs GET /api/audit/verify and shows the result inline.
export default function VerifyChain({ onVerified }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const run = async () => {
    setBusy(true)
    setError('')
    try {
      const r = await api.verifyChain()
      setResult(r)
      toast({ tone: r.valid ? 'success' : 'error', title: r.valid ? 'Audit chain valid' : 'Audit chain broken', message: r.message })
      onVerified?.(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="row" style={{ flexWrap: 'wrap' }}>
        <Button icon={ShieldCheck} loading={busy} onClick={run}>
          Verify audit chain
        </Button>
        <span className="faint">Recomputes every hash link, oldest to newest.</span>
      </div>
      <div role="status" aria-live="polite">
        {result && (
          <div className={`callout mt ${result.valid ? '' : 'danger'}`}>
            {result.valid ? <ShieldCheck size={18} aria-hidden="true" /> : <ShieldAlert size={18} aria-hidden="true" />}
            <span>
              <strong>{result.message}.</strong> {result.checked} {result.checked === 1 ? 'entry' : 'entries'} checked.
              {!result.valid && result.failure_at != null && ` First broken link: entry #${result.failure_at}.`}
            </span>
          </div>
        )}
        {error && (
          <div className="callout danger mt" role="alert">
            <ShieldAlert size={18} aria-hidden="true" />
            <span>Verification could not run: {error}</span>
          </div>
        )}
      </div>
    </div>
  )
}

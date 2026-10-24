import { useCallback, useEffect, useRef, useState } from 'react'
import { RefreshCcw } from 'lucide-react'
import { api } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { Button, Card, ProgressBar, useToast } from '../ui'
import { Callout } from './index'

/** Starts a retraining run from moderator decisions and follows it to the end. */
export function RetrainCard({ labels, onDone }) {
  const { user } = useAuth()
  const toast = useToast()
  const [job, setJob] = useState(null)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)
  const timer = useRef(null)
  const finished = useRef(false)

  const poll = useCallback(async () => {
    try {
      const s = await api.retrainStatus()
      setJob(s)
      if (s.state === 'running') {
        timer.current = setTimeout(poll, 1500)
      } else if (s.state === 'done' && !finished.current) {
        finished.current = true
        toast({ kind: 'success', title: 'Retraining finished', message: 'Scores and botnet clusters now use your decisions.' })
        onDone?.()
      } else if (s.state === 'error' && !finished.current) {
        finished.current = true
        toast({ kind: 'error', title: 'Retraining failed', message: s.message })
      }
    } catch (e) {
      setError(e.message)
    }
  }, [onDone, toast])

  useEffect(() => {
    api.retrainStatus().then((s) => {
      setJob(s)
      if (s.state === 'running') {
        finished.current = false
        poll()
      }
    }).catch(() => {})
    return () => clearTimeout(timer.current)
  }, [poll])

  const start = async () => {
    setError('')
    setStarting(true)
    try {
      await api.retrain()
      finished.current = false
      setJob({ state: 'running', progress: 0, message: 'Starting…' })
      poll()
    } catch (e) {
      setError(e.message)
    } finally {
      setStarting(false)
    }
  }

  const running = job?.state === 'running'
  return (
    <Card title="Next training run" subtitle="Moderator decisions become training labels. The test split is never touched, so before and after stay comparable.">
      <div className="stack" style={{ '--gap': '14px' }}>
        <p>
          <b className="num">{labels}</b> labelled account{labels === 1 ? '' : 's'} ready to learn from.
        </p>
        {error && (
          <Callout tone="error" title="Could not retrain">
            {error}
          </Callout>
        )}
        {running && (
          <div className="run-bar">
            <ProgressBar value={job.progress || 0.02} tone="lavender" label="Retraining progress" />
            <span className="small muted" role="status">
              {job.message}
            </span>
          </div>
        )}
        {job?.state === 'done' && !running && <Callout tone="success" title="Up to date">{job.message}</Callout>}
        {user?.role === 'moderator' ? (
          <Button icon={RefreshCcw} onClick={start} loading={running || starting} disabled={labels === 0}>
            {running ? 'Retraining…' : 'Retrain with decisions'}
          </Button>
        ) : (
          <p className="small muted">Only moderators can start a retraining run.</p>
        )}
        {labels === 0 && user?.role === 'moderator' && <p className="small muted">Confirm or dismiss at least one account to enable retraining.</p>}
      </div>
    </Card>
  )
}

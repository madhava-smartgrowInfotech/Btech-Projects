import { ErrorState } from '../components/ui'
import { useMonitor } from '../state/MonitorContext'

/** Banner-style error for a failed prediction/simulation; dismiss clears it, retry re-checks the API. */
export function PipelineError() {
  const { error, clearError, refreshHealth, health } = useMonitor()
  if (!error) return null
  return (
    <div style={{ marginBottom: 24 }}>
      <ErrorState
        title={error.status === 0 ? 'Cannot reach the ResQAI API' : 'The reading could not be processed'}
        error={error}
        hint={
          error.status === 0
            ? 'The Flask backend is not answering on port 8302. Start it with run.bat, then retry.'
            : 'The backend rejected the values. Check them and run the detection again.'
        }
        onRetry={() => {
          clearError()
          if (health.status !== 'ok') refreshHealth()
        }}
      />
    </div>
  )
}

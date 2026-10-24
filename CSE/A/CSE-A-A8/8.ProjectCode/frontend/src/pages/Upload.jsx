import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, FileSearch, RotateCcw, ScanText } from 'lucide-react'
import { api } from '../lib/api'
import { useConfig } from '../lib/config'
import { bytes } from '../lib/format'
import { Button, Card, CardHeader, ErrorState, FileDrop, PageHeader, ProgressBar, Stepper, Switch, useToast } from '../components/ui'
import { Callout, Disclaimer, ResultsTable } from '../components/lab'

const STEPS = ['Upload', 'Text extraction', 'Test-value extraction', 'Result classification', 'Database storage', 'AI health insights']

export default function Upload() {
  const toast = useToast()
  const { config } = useConfig()
  const [picked, setPicked] = useState(null)
  const [useLlm, setUseLlm] = useState(false)
  const [phase, setPhase] = useState('idle') // idle | uploading | processing | done | failed
  const [sent, setSent] = useState(0)
  const [outcome, setOutcome] = useState(null)
  const [failure, setFailure] = useState(null)

  const llmOk = !!config?.llm_available
  const accept = (config?.supported_extensions || ['.pdf', '.jpg', '.jpeg', '.png']).join(',')
  const maxMb = config?.max_size_mb || 15

  const reset = () => {
    setPhase('idle')
    setOutcome(null)
    setFailure(null)
    setSent(0)
  }

  const process = async () => {
    if (!picked) return
    setPhase('uploading')
    setSent(0)
    setOutcome(null)
    setFailure(null)
    try {
      const res = await api.uploadReport(picked.file, useLlm && llmOk, (p) => {
        setSent(p)
        if (p >= 1) setPhase('processing')
      })
      setOutcome(res)
      if (res.status === 'Completed') {
        setPhase('done')
        toast({ title: 'Report processed', message: `${res.results.length} test results extracted from ${picked.name}.` })
      } else {
        setPhase('failed')
        toast({ title: 'Processing failed', message: res.error || 'The report could not be processed.', tone: 'error' })
      }
    } catch (err) {
      setFailure(err)
      setPhase('failed')
      toast({ title: 'Upload failed', message: err.message, tone: 'error' })
    }
  }

  const busy = phase === 'uploading' || phase === 'processing'
  const done = outcome?.stages_completed?.length || 0
  const current = phase === 'idle' ? -1 : phase === 'uploading' ? 0 : phase === 'processing' ? 1 : done + 1
  const abnormal = outcome?.results?.filter((r) => r.status === 'LOW' || r.status === 'HIGH').length || 0

  return (
    <div className="container">
      <PageHeader title="Upload report" description={`Supported formats: PDF, JPG, JPEG, PNG (up to ${maxMb} MB).`} />

      <div className="upload-grid">
        <div className="stack">
          <Card pad>
            <FileDrop
              accept={accept}
              maxBytes={maxMb * 1024 * 1024}
              label="Drop a lab report here or click to browse"
              hint={`PDF, JPG, JPEG or PNG · up to ${maxMb} MB`}
              disabled={busy}
              onFile={(f) => {
                setPicked(f)
                if (phase !== 'idle') reset()
              }}
            />
            <div style={{ marginTop: 16 }}>
              <Switch label="Use LLM for richer explanations" checked={useLlm && llmOk} disabled={!llmOk || busy} onChange={(e) => setUseLlm(e.target.checked)} />
              <p className="stage-note">
                {llmOk
                  ? 'Abnormal results are rewritten in warmer language. Falls back to the built-in explanation if the model call fails.'
                  : config
                    ? 'Not available: no ANTHROPIC_API_KEY is configured on the server, so built-in explanations are used.'
                    : 'Checking server configuration…'}
              </p>
            </div>
            <div className="row" style={{ marginTop: 18 }}>
              <Button variant="primary" size="lg" icon={ScanText} loading={busy} disabled={!picked || busy} onClick={process}>
                {busy ? (phase === 'uploading' ? 'Uploading…' : 'Processing…') : 'Process report'}
              </Button>
              {phase !== 'idle' && !busy && (
                <Button icon={RotateCcw} onClick={reset}>
                  Start over
                </Button>
              )}
            </div>
            {busy && (
              <div style={{ marginTop: 18 }} aria-live="polite">
                {phase === 'uploading' ? (
                  <ProgressBar value={sent} label="Uploading" valueLabel={picked ? `${bytes(picked.size * sent)} of ${bytes(picked.size)}` : ''} />
                ) : (
                  <ProgressBar indeterminate label="Running OCR, extraction and classification" />
                )}
              </div>
            )}
          </Card>

          {phase === 'failed' && (
            <ErrorState
              title="This report could not be processed"
              error={failure || new Error(outcome?.error || 'Unknown error')}
              onRetry={picked ? process : undefined}
            >
              <p className="faint" style={{ maxWidth: '52ch' }}>
                Check that the file is a clear, upright lab report with rows like “Hemoglobin 13.5 g/dL 12 - 16”. Scanned images also need the Tesseract OCR program installed on the server.
              </p>
            </ErrorState>
          )}
        </div>

        <Card>
          <CardHeader title="Pipeline" subtitle="Each stage runs on the server in order." />
          <div className="card-body stepper-vertical">
            <Stepper steps={STEPS} current={current} />
          </div>
        </Card>
      </div>

      {phase === 'done' && outcome && (
        <div className="stack mt">
          <Callout tone="safe" icon={FileSearch} title="Report processed successfully.">
            Stages completed: {outcome.stages_completed.join(', ')}. {abnormal ? `${abnormal} result${abnormal === 1 ? ' is' : 's are'} outside the reference range.` : 'All results are within the reference range.'}
          </Callout>
          <Card>
            <CardHeader
              title="Extracted & classified results"
              subtitle={`${outcome.results.length} tests found`}
              actions={
                <Button as={Link} to={`/app/analysis/${outcome.report_id}`} variant="primary" size="sm" iconRight={ArrowRight}>
                  Open full analysis
                </Button>
              }
            />
            <ResultsTable results={outcome.results} />
          </Card>
          <Card pad>
            <details className="disclose">
              <summary>Show raw extracted text</summary>
              <pre className="rawtext">{outcome.raw_text || 'No text was extracted.'}</pre>
            </details>
          </Card>
        </div>
      )}

      <div className="mt">
        <Disclaimer />
      </div>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, ScanSearch, XCircle } from 'lucide-react'
import { Button, Card, CardHeader, Container, FileDrop, Input, PageHeader, ProgressBar, Switch, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import AnalysisResult from '../components/AnalysisResult'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'

const MAX_MB = 20

export default function Analyze() {
  const toast = useToast()
  const { refresh } = useStats()
  const [file, setFile] = useState(null)
  const [opts, setOpts] = useState({ activeOnly: true, minScore: 0, topic: '', method: '' })
  const [busy, setBusy] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const abort = useRef(null)
  const resultRef = useRef(null)

  useEffect(() => {
    if (!busy) return undefined
    const start = Date.now()
    const t = setInterval(() => setElapsed(Math.round((Date.now() - start) / 1000)), 500)
    return () => clearInterval(t)
  }, [busy])

  useEffect(() => () => abort.current?.abort(), [])

  const minErr = opts.minScore !== '' && (Number(opts.minScore) < 0 || Number(opts.minScore) > 100) ? 'Enter a score between 0 and 100.' : null

  const run = async () => {
    if (!file?.file) {
      setError(new Error('Choose a PDF file first.'))
      return
    }
    if (minErr) return
    setError(null)
    setResult(null)
    setBusy(true)
    setElapsed(0)
    abort.current = new AbortController()
    try {
      const r = await api.analyze(file.file, { ...opts, minScore: Number(opts.minScore) || 0 }, abort.current.signal)
      setResult(r)
      refresh()
      toast({ title: 'Analysis complete', message: `${r.filename} was analyzed and saved as #${r.analysis_id}.` })
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60)
    } catch (e) {
      if (e?.name === 'AbortError') {
        toast({ title: 'Analysis cancelled', message: 'The upload was cancelled before a result came back.', tone: 'info' })
      } else {
        setError(e)
        toast({ title: 'Analysis failed', message: e.message, tone: 'error' })
      }
    } finally {
      setBusy(false)
      abort.current = null
    }
  }

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Analyze paper' }]}
        title="Analyze a paper"
        description="PDF → extraction → decision signal → local AI critique → literature context → reviewer matching → auditable recommendation."
      />
      <SlideUp>
        <Card>
          <CardHeader title="1 · Upload" subtitle={`PDF only, up to ${MAX_MB} MB. Text is extracted locally on this machine.`} />
          <div className="card-body stack" style={{ gap: 20 }}>
            <FileDrop
              accept=".pdf,application/pdf"
              label="Drop a research-paper PDF here or click to browse"
              hint={`.pdf · max ${MAX_MB} MB · scanned image-only PDFs yield very little text`}
              maxBytes={MAX_MB * 1048576}
              readText={false}
              disabled={busy}
              onFile={(f) => {
                setFile(f)
                setError(null)
              }}
            />
            <div>
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>2 · Reviewer-matching filters</h3>
              <div className="filters">
                <div className="switch-field">
                  <Switch label="Active reviewers only" checked={opts.activeOnly} onChange={(e) => setOpts({ ...opts, activeOnly: e.target.checked })} disabled={busy} />
                </div>
                <Input label="Minimum score (0-100)" type="number" min="0" max="100" value={opts.minScore} error={minErr} onChange={(e) => setOpts({ ...opts, minScore: e.target.value })} disabled={busy} />
                <Input label="Topic contains" placeholder="e.g. vision" value={opts.topic} onChange={(e) => setOpts({ ...opts, topic: e.target.value })} disabled={busy} />
                <Input label="Method contains" placeholder="e.g. transformer" value={opts.method} onChange={(e) => setOpts({ ...opts, method: e.target.value })} disabled={busy} />
              </div>
            </div>

            {busy && (
              <div className="analyzing" role="status" aria-live="polite">
                <ProgressBar indeterminate label="Analyzing your paper…" valueLabel={`${elapsed}s`} />
                <p className="faint">
                  Extraction, the decision model, the local AI review and the literature lookup run on this machine&apos;s CPU and can take a minute or more the first time (the language model is loaded on demand).
                </p>
              </div>
            )}
            {error && !busy && (
              <div className="note danger" role="alert">
                <XCircle size={18} aria-hidden="true" />
                <span>
                  <strong>Analysis failed.</strong> {error.message}
                  {error.offline ? '' : ' Check the file and try again, or try another PDF.'}
                </span>
              </div>
            )}

            <div className="row">
              {busy ? (
                <Button onClick={() => abort.current?.abort()}>Cancel</Button>
              ) : (
                <Button variant="primary" icon={ScanSearch} disabled={!file} onClick={run}>
                  Analyze paper
                </Button>
              )}
              {!file && !busy && <span className="faint">Choose a PDF to enable analysis.</span>}
            </div>
          </div>
        </Card>
      </SlideUp>

      <div ref={resultRef} style={{ scrollMarginTop: 80 }}>
        {result && (
          <SlideUp>
            <div className="row mt" style={{ justifyContent: 'space-between' }}>
              <h2 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 size={20} aria-hidden="true" style={{ color: 'var(--safe)' }} /> Result for {result.filename}
              </h2>
              <Button as={Link} to="/app/history" size="sm" variant="ghost">
                View in history
              </Button>
            </div>
            <div className="mt">
              <AnalysisResult result={result} id={result.analysis_id} />
            </div>
          </SlideUp>
        )}
      </div>
    </Container>
  )
}

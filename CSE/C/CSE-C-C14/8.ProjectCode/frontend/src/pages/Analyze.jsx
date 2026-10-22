import { useEffect, useState } from 'react'
import { Lock, Play, ScanSearch, Square, Timer, X } from 'lucide-react'
import { api } from '../lib/api'
import { useLoad, useDocTitle } from '../lib/hooks'
import { useAnalysis } from '../lib/analysis'
import { Badge, Button, Card, ErrorState, FileDrop, PageHeader, ProgressBar, Timeline, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import ResultView from '../components/ResultView'

const FALLBACK = { max_mb: 10, allowed_extensions: ['png', 'jpg', 'jpeg', 'webp'] }

function Elapsed({ since }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 500)
    return () => clearInterval(t)
  }, [])
  return <span className="num">{Math.max(0, Math.round((now - since) / 1000))}s</span>
}

export default function Analyze() {
  useDocTitle('Analyze image · VeriVision AI')
  const toast = useToast()
  const a = useAnalysis()
  const cfg = useLoad((s) => api.config(s), [])
  const limits = cfg.data || FALLBACK
  const [problem, setProblem] = useState('')
  const [dropKey, setDropKey] = useState(0)

  const reject = (msg) => {
    setProblem(msg)
    a.choose(null)
    setDropKey((k) => k + 1)
  }

  const onFiles = (files) => {
    const f = files[0]
    if (!f) {
      setProblem('')
      return a.choose(null)
    }
    const ext = f.name.includes('.') ? f.name.split('.').pop().toLowerCase() : ''
    if (!limits.allowed_extensions.includes(ext)) {
      return reject(`“${f.name}” is not supported. Choose a ${limits.allowed_extensions.join(', ').toUpperCase()} image.`)
    }
    if (f.size > limits.max_mb * 1024 * 1024) {
      return reject(`“${f.name}” is ${(f.size / 1048576).toFixed(1)} MB. The limit is ${limits.max_mb} MB - choose a smaller image.`)
    }
    setProblem('')
    a.choose(f)
  }

  const analyze = async () => {
    try {
      const r = await a.run(a.file)
      if (r) toast({ kind: 'success', title: 'Analysis complete', message: `${r.confidence_word} · ${r.agreement_count}/4 branches agree.` })
    } catch (e) {
      toast({ kind: 'error', title: 'Analysis failed', message: e.message })
    }
  }

  const again = () => {
    a.reset()
    setProblem('')
    setDropKey((k) => k + 1)
  }

  if (a.status === 'done' && a.result) return <ResultView result={a.result} onAgain={again} />

  const running = a.status === 'running'
  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="Analyzer"
        icon={ScanSearch}
        title="Is this image real or AI-generated?"
        lead="Upload one image. Four detectors vote, Grad-CAM shows where they looked, and a robustness check tells you how much to trust the answer."
      />
      <div className="grid-2 wide-left">
        <SlideUp>
          <Card hover={false} title="Choose an image" subtitle={`PNG, JPG/JPEG or WEBP · up to ${limits.max_mb} MB · processed on this machine`}>
            <div className="stack" style={{ '--gap': '16px' }}>
              {!running && (
                <FileDrop
                  key={dropKey}
                  accept={limits.allowed_extensions.map((e) => `.${e}`).join(',')}
                  onFiles={onFiles}
                  label="Drop an image here or click to browse"
                  hint="Press Enter or Space to open the file picker"
                />
              )}
              {problem && (
                <div className="card tint-peach small" role="alert" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <X size={18} aria-hidden="true" /> {problem}
                </div>
              )}
              {a.previewUrl && (
                <figure style={{ margin: 0 }}>
                  <img
                    src={a.previewUrl}
                    alt={`Preview of ${a.file?.name}`}
                    style={{ width: '100%', maxHeight: 340, objectFit: 'contain', borderRadius: 18, background: 'var(--surface-2)', border: '1px solid var(--border)' }}
                  />
                  <figcaption className="small muted" style={{ marginTop: 6 }}>
                    {a.file?.name} · {(a.file?.size / 1024).toFixed(1)} KB
                  </figcaption>
                </figure>
              )}
              {running && (
                <div className="stack" style={{ '--gap': '10px' }} role="status" aria-live="polite">
                  <ProgressBar indeterminate label="Analyzing image" />
                  <p className="small">
                    Running 4 detectors, Grad-CAM and robustness variants… <Timer size={14} aria-hidden="true" style={{ verticalAlign: -2 }} />{' '}
                    <Elapsed since={a.startedAt} />
                  </p>
                  <p className="small muted">This can take up to a minute on a CPU. You can leave this screen - the result will be waiting.</p>
                </div>
              )}
              {a.status === 'error' && (
                <ErrorState
                  compact
                  title="We couldn't analyze that image"
                  error={a.error}
                  hint={
                    a.error?.status === 401
                      ? 'Your session expired - sign in again.'
                      : a.error?.status === 0
                        ? undefined
                        : 'Try a different image, or check System status.'
                  }
                  onRetry={a.file ? analyze : undefined}
                />
              )}
              <div className="row">
                {running ? (
                  <Button variant="secondary" icon={Square} onClick={a.cancel}>Cancel</Button>
                ) : (
                  <Button size="lg" icon={Play} onClick={analyze} disabled={!a.file}>Analyze image</Button>
                )}
                {!a.file && !running && <span className="small muted">Pick an image to enable analysis.</span>}
              </div>
            </div>
          </Card>
        </SlideUp>
        <SlideUp delay={0.08}>
          <Card hover={false} tint="lavender" title="What happens next">
            <Timeline
              animate={false}
              items={[
                { title: 'Four detectors vote', meta: 'EfficientNet ×2, ResNet50 and MobileNetV3 each classify the image.', tone: 'lavender' },
                { title: 'Votes are fused', meta: 'Weighted logit fusion, with two gates that handle outliers and consensus.', tone: 'mint' },
                { title: 'Grad-CAM explains', meta: 'Heatmaps show which regions drove the prediction.', tone: 'peach' },
                { title: 'Robustness check', meta: 'JPEG, resize and blur variants test how stable the verdict is.', tone: 'sky' },
              ]}
            />
            <p className="small muted" style={{ marginTop: 18, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <Lock size={14} aria-hidden="true" /> Your image stays on this machine. <Badge tone="neutral">AI estimate, not proof</Badge>
            </p>
          </Card>
        </SlideUp>
      </div>
    </div>
  )
}

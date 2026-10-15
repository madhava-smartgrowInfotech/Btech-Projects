import { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import { useReducedMotion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  CheckCircle2,
  Cpu,
  Download,
  FileJson,
  ImageOff,
  Info,
  RefreshCw,
  ScanSearch,
  SearchX,
  SlidersHorizontal,
  TriangleAlert,
  Zap,
} from 'lucide-react'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  FileDrop,
  PageHeader,
  ProgressBar,
  Skeleton,
  StatCard,
  Switch,
  Table,
  useToast,
} from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useHealth } from '../lib/health'
import { PREPROCESS_STEPS } from '../content'

const DEFAULT_CONF = 0.5

function stem(name) {
  return name.replace(/\.[^.]+$/, '')
}

function download(href, filename) {
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
}

function ModelNotice({ health, error, onReload, reloading }) {
  if (error) {
    return (
      <div className="notice warn" role="alert">
        <TriangleAlert size={20} aria-hidden="true" />
        <div>
          <strong>The API is not reachable</strong>
          <p>Start it with run.bat, then this panel updates by itself.</p>
        </div>
      </div>
    )
  }
  if (!health) return <Skeleton height={72} radius={18} />
  const m = health.model
  if (m.status === 'error') {
    return (
      <div className="notice warn" role="alert">
        <TriangleAlert size={20} aria-hidden="true" />
        <div>
          <strong>Model failed to load</strong>
          <p>{m.error}</p>
          <Button size="sm" variant="secondary" icon={RefreshCw} loading={reloading} onClick={onReload} style={{ marginTop: 10 }}>
            Try loading again
          </Button>
        </div>
      </div>
    )
  }
  if (!m.ready) {
    return (
      <div className="notice info" role="status">
        <Info size={20} aria-hidden="true" />
        <div>
          <strong>Loading the YOLO model…</strong>
          <p>The first start can take a moment. You can already upload an image; detection runs as soon as the model is ready.</p>
        </div>
      </div>
    )
  }
  if (m.used_fallback) {
    return (
      <div className="notice warn">
        <TriangleAlert size={20} aria-hidden="true" />
        <div>
          <strong>Placeholder model in use</strong>
          <p>{m.message}</p>
        </div>
      </div>
    )
  }
  return (
    <div className="notice ok">
      <CheckCircle2 size={20} aria-hidden="true" />
      <div>
        <strong>Trained model loaded</strong>
        <p>{m.message}</p>
      </div>
    </div>
  )
}

const COLUMNS = [
  { key: 'index', label: 'Object', numeric: true },
  { key: 'class_name', label: 'Class' },
  { key: 'confidence', label: 'Confidence', numeric: true, sortValue: (r) => r.confidence, render: (r) => `${r.confidence_percent.toFixed(1)}%` },
  { key: 'bbox', label: 'BBox (x1,y1,x2,y2)', sortable: false, render: (r) => `(${r.bbox.join(', ')})` },
]

export default function Detection() {
  const toast = useToast()
  const reduce = useReducedMotion()
  const health = useHealth()
  const confId = useId()
  const dropKey = useRef(0)

  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [conf, setConf] = useState(DEFAULT_CONF)
  const [preprocess, setPreprocess] = useState(true)
  const [phase, setPhase] = useState('idle') // idle | running | done | error
  const [result, setResult] = useState(null)
  const [ranWith, setRanWith] = useState(null)
  const [error, setError] = useState(null)
  const [reloading, setReloading] = useState(false)
  const seq = useRef(0)

  useEffect(() => {
    document.title = 'Detection · PlastiScan'
  }, [])

  // keep an object URL for the original image preview
  useEffect(() => {
    if (!file || !file.type.startsWith('image/')) {
      setPreviewUrl(null)
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const run = useCallback(
    async (f, c, p) => {
      const id = ++seq.current
      setPhase('running')
      setError(null)
      try {
        const data = await api.detect({ file: f, conf: c, preprocess: p })
        if (id !== seq.current) return
        setResult(data)
        setRanWith({ conf: c, preprocess: p })
        setPhase('done')
        if (data.detection_count > 0) {
          toast({ kind: 'success', title: `${data.detection_count} object${data.detection_count === 1 ? '' : 's'} detected`, message: 'The run was saved to your detection history.' })
          if (!reduce) {
            import('canvas-confetti').then(({ default: confetti }) =>
              confetti({ particleCount: 60, spread: 70, origin: { y: 0.35 }, colors: ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF'], disableForReducedMotion: true }),
            )
          }
        } else {
          toast({ kind: 'info', title: 'No objects detected', message: 'Nothing was above the current confidence threshold.' })
        }
      } catch (e) {
        if (id !== seq.current) return
        setError(e)
        setPhase('error')
        toast({ kind: 'error', title: 'Detection failed', message: e.message })
      }
    },
    [toast, reduce],
  )

  const onFiles = (list) => {
    const f = list[0] || null
    setFile(f)
    setResult(null)
    setRanWith(null)
    setError(null)
    if (f) run(f, conf, preprocess)
    else {
      seq.current += 1
      setPhase('idle')
    }
  }

  const reload = async () => {
    setReloading(true)
    try {
      await api.reloadModel()
      health.refresh()
    } catch (e) {
      toast({ kind: 'error', title: 'Could not restart model loading', message: e.message })
    } finally {
      setReloading(false)
    }
  }

  const changed = ranWith && (ranWith.conf !== conf || ranWith.preprocess !== preprocess)
  const fill = `${((conf - 0.1) / 0.8) * 100}%`

  const report = useMemo(
    () =>
      result && {
        image_name: result.filename,
        detection_count: result.detection_count,
        average_confidence_percent: result.average_confidence_percent,
        detections: result.rows,
        timestamp: result.timestamp,
      },
    [result],
  )

  const downloadReport = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }))
    download(url, `report_${stem(result.filename)}.json`)
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    toast({ kind: 'success', title: 'Report downloaded', message: `report_${stem(result.filename)}.json` })
  }

  const downloadImage = () => {
    download(result.annotated_image, `detected_${stem(result.filename)}.jpg`)
    toast({ kind: 'success', title: 'Image downloaded', message: `detected_${stem(result.filename)}.jpg` })
  }

  const badRequest = error && (error.status === 400 || error.status === 413 || error.status === 422)
  const lowerTo = Math.max(0.1, Math.round((conf - 0.1) * 20) / 20)

  return (
    <div className="stack" style={{ '--gap': '8px' }}>
      <PageHeader
        eyebrow="Detection"
        icon={ScanSearch}
        title="Find plastic in an ocean image"
        lead="Upload an ocean or water image to detect and localise plastic waste. Every item gets a bounding box and a confidence score."
      />

      <div className="detect-grid">
        <div className="side-stack">
          <Card title="1 · Upload an image" subtitle="JPG, JPEG or PNG" hover={false}>
            <FileDrop
              key={dropKey.current}
              accept=".jpg,.jpeg,.png,image/jpeg,image/png"
              onFiles={onFiles}
              label="Drop an ocean image here or click to browse"
              hint="JPG, JPEG or PNG · up to 25 MB"
            />
          </Card>

          <Card title="2 · Settings" hover={false}>
            <div className="stack" style={{ '--gap': '18px' }}>
              <div>
                <div className="range-row">
                  <label className="field-label" htmlFor={confId}>
                    Confidence threshold
                  </label>
                  <output htmlFor={confId}>{conf.toFixed(2)}</output>
                </div>
                <input
                  id={confId}
                  className="range"
                  type="range"
                  min="0.1"
                  max="0.9"
                  step="0.05"
                  value={conf}
                  style={{ '--fill': fill }}
                  onChange={(e) => setConf(Number(e.target.value))}
                  aria-describedby={`${confId}-hint`}
                />
                <div className="range-scale" aria-hidden="true">
                  <span>0.10 · more boxes</span>
                  <span>0.90 · fewer, surer</span>
                </div>
                <span className="field-hint" id={`${confId}-hint`}>
                  Only detections above this confidence score are shown.
                </span>
              </div>

              <div>
                <Switch
                  checked={preprocess}
                  onChange={setPreprocess}
                  label="Apply preprocessing pipeline"
                  description="Colour correction, denoising and contrast boost before detection"
                />
                {preprocess && (
                  <ol className="pipeline" aria-label="Preprocessing steps">
                    {PREPROCESS_STEPS.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ol>
                )}
              </div>

              <div className="stack" style={{ '--gap': '10px' }}>
                {changed && (
                  <Badge tone="peach" icon={SlidersHorizontal}>
                    Settings changed since the last run
                  </Badge>
                )}
                <Button
                  block
                  icon={Zap}
                  loading={phase === 'running'}
                  disabled={!file}
                  onClick={() => run(file, conf, preprocess)}
                  variant={changed ? 'primary' : 'secondary'}
                >
                  {phase === 'running' ? 'Detecting…' : result ? 'Run detection again' : 'Run detection'}
                </Button>
                {!file && <span className="field-hint">Choose an image first.</span>}
              </div>
            </div>
          </Card>

          <Card
            title="Model"
            actions={
              health.data && (
                <Badge tone="lavender" icon={Cpu}>
                  {health.data.device === 'cuda' ? 'GPU (CUDA)' : 'CPU'}
                </Badge>
              )
            }
            hover={false}
          >
            <ModelNotice health={health.data} error={health.error} onReload={reload} reloading={reloading} />
          </Card>
        </div>

        <div className="stack" aria-live="polite">
          {phase === 'idle' && !file && (
            <EmptyState
              icon={ImageOff}
              tone="sky"
              title="No image analysed yet"
              message="Upload a JPG, JPEG or PNG ocean image to begin. The original and the annotated image will appear here side by side."
              action={
                <Button variant="secondary" onClick={() => document.querySelector('.filedrop')?.focus()}>
                  Go to the upload box
                </Button>
              }
            />
          )}

          {phase === 'running' && (
            <Card hover={false} aria-busy="true">
              <div className="stack">
                <ProgressBar indeterminate label="Running detection" />
                <p className="small muted" role="status">
                  Preprocessing and running detection - the first image after start-up is the slowest.
                </p>
                <div className="compare">
                  <figure className="shot">
                    {previewUrl ? <img src={previewUrl} alt={`Original upload: ${file?.name}`} /> : <Skeleton height={260} radius={0} />}
                    <figcaption>Original</figcaption>
                  </figure>
                  <Skeleton height={300} radius={18} />
                </div>
                <Skeleton height={90} radius={18} />
              </div>
            </Card>
          )}

          {phase === 'error' && (
            <ErrorState
              title={badRequest ? 'We could not use that image' : 'Detection failed'}
              error={error}
              hint={
                badRequest
                  ? 'Upload a .jpg, .jpeg or .png file that opens normally on your computer, up to 25 MB.'
                  : error?.status === 0
                    ? 'Start the API with run.bat, then try again.'
                    : 'Check the model panel on the left, then try again.'
              }
              onRetry={file && !badRequest ? () => run(file, conf, preprocess) : undefined}
            />
          )}

          {phase === 'done' && result && (
            <Stagger className="stack">
              <Stagger.Item className="grid-kpi">
                <StatCard label="Detected plastic objects" value={result.detection_count} icon={ScanSearch} tone="mint" foot={`in ${result.filename}`} />
                <StatCard
                  label="Average confidence"
                  display={result.detection_count ? `${result.average_confidence_percent.toFixed(1)}%` : '–'}
                  icon={Zap}
                  tone="lavender"
                  foot={`threshold ${result.conf_threshold.toFixed(2)}`}
                />
                <StatCard
                  label="Image preparation"
                  display={result.preprocessed ? 'Enhanced' : 'Raw'}
                  icon={SlidersHorizontal}
                  tone="peach"
                  foot={`${result.preprocessed ? 'preprocessing on' : 'preprocessing off'} · ${result.image_size.width} × ${result.image_size.height} px`}
                />
              </Stagger.Item>

              {result.model.used_fallback && (
                <Stagger.Item className="notice warn">
                  <TriangleAlert size={20} aria-hidden="true" />
                  <div>
                    <strong>Detected with the COCO placeholder model</strong>
                    <p>These boxes come from a general-purpose model, not a plastic-waste model, so classes such as “bottle” or “person” are not reliable plastic detections.</p>
                  </div>
                </Stagger.Item>
              )}

              <Stagger.Item>
                <Card hover={false}>
                  <div className="compare">
                    <div>
                      <div className="shot-title">Original image</div>
                      <figure className="shot">
                        {previewUrl && <img src={previewUrl} alt={`Original upload: ${result.filename}`} />}
                        <figcaption>{result.filename}</figcaption>
                      </figure>
                    </div>
                    <div>
                      <div className="shot-title">Detected image</div>
                      <figure className="shot">
                        <img src={result.annotated_image} alt={`Annotated result with ${result.detection_count} detected objects`} />
                        <figcaption>
                          <span>
                            {result.detection_count} box{result.detection_count === 1 ? '' : 'es'} drawn
                          </span>
                          <span>{result.timestamp}</span>
                        </figcaption>
                      </figure>
                    </div>
                  </div>
                </Card>
              </Stagger.Item>

              {result.detection_count === 0 ? (
                <Stagger.Item>
                  <EmptyState
                    icon={SearchX}
                    tone="peach"
                    title="No objects detected above this threshold"
                    message="Try lowering the confidence threshold. This can also mean the model has not been trained on a plastic-waste dataset yet."
                    action={
                      conf > 0.1 ? (
                        <Button
                          icon={SlidersHorizontal}
                          onClick={() => {
                            setConf(lowerTo)
                            run(file, lowerTo, preprocess)
                          }}
                        >
                          Lower threshold to {lowerTo.toFixed(2)} and retry
                        </Button>
                      ) : null
                    }
                  />
                </Stagger.Item>
              ) : (
                <>
                  <Stagger.Item>
                    <div className="grid-2">
                      <Card title="Confidence scores" subtitle="Most confident first" hover={false}>
                        <ol className="score-list">
                          {result.detections.map((d) => (
                            <li key={d.index}>
                              <div className="score-top">
                                <span>Plastic {d.index}</span>
                                <span className="num">{d.confidence_percent.toFixed(1)}%</span>
                              </div>
                              <ProgressBar value={d.confidence} tone="mint" label={`Plastic ${d.index} confidence`} />
                            </li>
                          ))}
                        </ol>
                      </Card>
                      <Card title="Export" subtitle="Take the results with you" hover={false}>
                        <div className="stack" style={{ '--gap': '12px' }}>
                          <Button icon={Download} onClick={downloadImage}>
                            Download detection image
                          </Button>
                          <Button variant="secondary" icon={FileJson} onClick={downloadReport}>
                            Download report (JSON)
                          </Button>
                          <div className="notice ok" role="status">
                            <CheckCircle2 size={20} aria-hidden="true" />
                            <div>
                              <strong>Logged to detection history</strong>
                              <p>
                                Saved as <span className="mono">{result.saved_as}</span> in results/. See it on the{' '}
                                <Link to="/app/dashboard" style={{ fontWeight: 600 }}>
                                  Dashboard
                                </Link>
                                .
                              </p>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </div>
                  </Stagger.Item>

                  <Stagger.Item>
                    <Card title="Detection table" hover={false}>
                      <Table
                        columns={COLUMNS}
                        rows={result.detections}
                        rowKey={(r) => r.index}
                        pageSize={8}
                        caption="Detected objects"
                        cardTitle={(r) => `Object ${r.index}`}
                      />
                    </Card>
                  </Stagger.Item>
                </>
              )}
            </Stagger>
          )}
        </div>
      </div>
    </div>
  )
}

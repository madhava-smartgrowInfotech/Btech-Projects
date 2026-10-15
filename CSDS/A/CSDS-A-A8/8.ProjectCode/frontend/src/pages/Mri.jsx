import { useMemo, useState } from 'react'
import { Activity, Brain, ChevronLeft, ChevronRight, Crosshair, Gauge, Layers, Maximize2, Percent, Play, Ruler, Sparkles } from 'lucide-react'
import { api, sampleUrl } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { fixed, num } from '../lib/format'
import { Badge, Button, Card, CardHeader, EmptyState, FileDrop, Input, PageHeader, Select, Skeleton, StatCard, Tabs, useToast } from '../components/ui'
import { Figure, LoadError, ReportCard } from '../components/bio'
import { FadeIn, Stagger } from '../components/motion'

const PAGE = 12
const MAX_UPLOAD = 10 * 1024 * 1024

export default function Mri() {
  const toast = useToast()
  const models = useAsync(() => api.get('/mri/models'), [])
  const samples = useAsync(() => api.get('/mri/samples'), [])

  const [model, setModel] = useState('')
  const [spacing, setSpacing] = useState('1.0')
  const [upload, setUpload] = useState(null)
  const [sample, setSample] = useState(null)
  const [page, setPage] = useState(0)
  const [view, setView] = useState('overlay')
  const [phase, setPhase] = useState({ loading: false, error: null, result: null })
  const [dropKey, setDropKey] = useState(0)

  const modelList = models.data || []
  const available = modelList.filter((m) => m.available)
  const activeModel = model || available.find((m) => m.key === 'jepa_10')?.key || available[0]?.key || ''
  const sampleList = samples.data || []
  const pageItems = sampleList.slice(page * PAGE, page * PAGE + PAGE)
  const pages = Math.max(1, Math.ceil(sampleList.length / PAGE))

  const spacingNum = Number(spacing)
  const spacingError = !(spacingNum >= 0.05 && spacingNum <= 5) ? 'Enter a value between 0.05 and 5 mm per pixel.' : ''
  const preview = useMemo(() => (upload ? upload.url : sample ? sampleUrl(sample) : null), [upload, sample])
  const hasInput = !!(upload || sample)
  const modelsReady = models.data && available.length > 0

  const pickSample = (name) => {
    setSample(name)
    setUpload(null)
    setDropKey((k) => k + 1)
    setPhase({ loading: false, error: null, result: null })
  }
  const pickUpload = (info) => {
    setUpload(info)
    if (info) setSample(null)
    setPhase({ loading: false, error: null, result: null })
  }

  const run = async () => {
    setPhase({ loading: true, error: null, result: null })
    setView('overlay')
    try {
      let result
      if (upload) {
        const form = new FormData()
        form.append('file', upload.file)
        form.append('model', activeModel)
        form.append('pixel_spacing_mm', String(spacingNum))
        result = await api.upload('/mri/segment', form)
      } else {
        result = await api.post('/mri/segment-sample', { name: sample, model: activeModel, pixel_spacing_mm: spacingNum })
      }
      setPhase({ loading: false, error: null, result })
      toast({ title: result.tumour_detected ? 'Tumour region segmented' : 'No tumour region found', message: 'The analysis was saved to your history.' })
    } catch (error) {
      setPhase({ loading: false, error, result: null })
    }
  }

  const { loading, error, result } = phase
  const firstTumour = sampleList.find((s) => s.tumour_pixels > 0)

  return (
    <div className="container">
      <PageHeader
        title="MRI analysis"
        description="Upload a brain-MRI slice or pick a held-out sample to get the tumour mask, its area and a structured report from the JEPA-pre-trained segmenter."
      />
      <div className="split split-mri">
        <Card pad className="stack" style={{ gap: 18 }}>
          {models.loading ? (
            <Skeleton height={44} />
          ) : models.error ? (
            <LoadError title="Could not load the models" error={models.error} onRetry={models.reload} />
          ) : (
            <>
              {!modelsReady && (
                <p className="callout danger" role="alert">
                  No trained segmentation model was found on the server, so slices cannot be analysed yet. Train the models with <code>ml/train_mri.py</code> and
                  copy the <code>mri_seg_*.pt</code> files into <code>models/</code>.
                </p>
              )}
              <Select
                label="Segmentation model"
                value={activeModel}
                onChange={(e) => setModel(e.target.value)}
                options={modelList.map((m) => ({ value: m.key, label: `${m.label}${m.available ? '' : ' (not trained)'}` }))}
                hint={modelsReady ? `${available.length} of ${modelList.length} models available.` : undefined}
              />
            </>
          )}
          <Input
            label="Pixel spacing (mm per pixel)"
            type="number"
            step="0.01"
            min="0.05"
            max="5"
            inputMode="decimal"
            value={spacing}
            onChange={(e) => setSpacing(e.target.value)}
            error={spacingError}
            hint="Used to convert the tumour area from pixels to mm²."
          />
          <div>
            <span className="field-label" style={{ display: 'block', marginBottom: 7 }}>
              Upload a slice
            </span>
            <FileDrop
              binary
              accept=".png,.jpg,.jpeg,.tif,.tiff"
              label="Drop a slice here or click to browse"
              hint="PNG, JPG or TIF, up to 10 MB"
              maxBytes={MAX_UPLOAD}
              resetKey={dropKey}
              onFile={pickUpload}
            />
          </div>
          <div>
            <div className="pager">
              <span className="field-label">Or pick a sample slice{sampleList.length ? ` (${sampleList.length})` : ''}</span>
              <div className="row" style={{ gap: 4 }}>
                <Button size="sm" variant="ghost" icon={ChevronLeft} aria-label="Previous samples" disabled={page === 0} onClick={() => setPage(page - 1)} />
                <span className="faint" aria-live="polite">
                  {page + 1}/{pages}
                </span>
                <Button size="sm" variant="ghost" icon={ChevronRight} aria-label="Next samples" disabled={page >= pages - 1} onClick={() => setPage(page + 1)} />
              </div>
            </div>
            {samples.loading ? (
              <div className="thumbs" aria-busy="true">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} height="auto" style={{ aspectRatio: '1' }} radius={8} />
                ))}
              </div>
            ) : samples.error ? (
              <LoadError title="Could not load sample slices" error={samples.error} onRetry={samples.reload} />
            ) : sampleList.length === 0 ? (
              <p className="faint">No sample slices are installed on the server.</p>
            ) : (
              <div className="thumbs">
                {pageItems.map((s, i) => (
                  <button
                    key={s.file}
                    type="button"
                    className="thumb"
                    aria-pressed={sample === s.file}
                    aria-label={`Sample slice ${page * PAGE + i + 1}${s.tumour_pixels ? ', tumour in the expert mask' : ', no tumour in the expert mask'}`}
                    title={s.tumour_pixels ? 'Tumour in the expert mask' : 'No tumour in the expert mask'}
                    onClick={() => pickSample(s.file)}
                  >
                    <img src={sampleUrl(s.file)} alt="" loading="lazy" />
                    {s.tumour_pixels > 0 && <span className="thumb-dot" />}
                  </button>
                ))}
              </div>
            )}
            <p className="faint" style={{ marginTop: 8 }}>
              Held-out LGG slices. A red dot means the expert mask contains a tumour.
            </p>
          </div>
          <Button variant="primary" size="lg" icon={Play} loading={loading} disabled={!hasInput || !modelsReady || !!spacingError || !activeModel} onClick={run}>
            {loading ? 'Segmenting and writing the report…' : 'Analyse slice'}
          </Button>
          {!hasInput && !loading && <p className="faint">Choose a slice to enable the analysis.</p>}
        </Card>

        <div className="stack">
          <Card pad>
            <div className="row" style={{ justifyContent: 'space-between', marginBottom: 14 }}>
              <h2 style={{ fontSize: 16 }}>Segmentation</h2>
              {result && (
                <Tabs
                  label="Result view"
                  value={view}
                  onChange={setView}
                  tabs={[
                    { value: 'overlay', label: 'Overlay', icon: Layers },
                    { value: 'mask', label: 'Mask', icon: Maximize2 },
                  ]}
                />
              )}
            </div>
            <div className="grid grid-2">
              <Figure title="Input slice" src={preview} placeholder="Pick or upload a slice to preview it here." />
              <Figure
                title={view === 'mask' ? 'Predicted mask' : 'Tumour overlay'}
                src={view === 'mask' ? result?.mask_png : result?.overlay_png}
                loading={loading}
                placeholder={error ? 'The analysis failed - see the message below.' : 'Run the analysis to see the mask.'}
              />
            </div>
            {result && (
              <p className="faint" style={{ marginTop: 10 }}>
                Yellow outline and red tint mark the predicted tumour region. Model: {result.model_label}.
              </p>
            )}
          </Card>

          {error && <LoadError title="The analysis failed" error={error} onRetry={hasInput ? run : undefined} hint={error.status === 400 ? 'Check the image and the model selection, then try again.' : undefined} />}

          {loading && (
            <div className="grid grid-4" aria-busy="true" aria-label="Running analysis">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} height={112} radius={12} />
              ))}
            </div>
          )}

          {!result && !loading && !error && (
            <Card>
              <EmptyState
                icon={Brain}
                title="No analysis yet"
                actions={
                  firstTumour && modelsReady ? (
                    <Button icon={Sparkles} onClick={() => pickSample(firstTumour.file)}>
                      Try a slice that contains a tumour
                    </Button>
                  ) : undefined
                }
              >
                Pick a slice on the left and run the analysis. You get the tumour overlay, area in px and mm², the share of the brain it covers and a structured report.
              </EmptyState>
            </Card>
          )}

          {result && (
            <FadeIn className="stack">
              <Stagger className="grid grid-4">
                <StatCard label="Tumour detected" value={result.tumour_detected ? 'Yes' : 'No'} icon={Activity} tone={result.tumour_detected ? 'danger' : undefined} delta={result.location} />
                <StatCard label="Area" value={result.area_mm2} format={(v) => `${num(v, 1)} mm²`} icon={Ruler} delta={`${num(result.area_pixels)} px`} />
                <StatCard label="Share of brain" value={result.percent_of_brain} format={(v) => `${num(v, 2)}%`} icon={Percent} />
                <StatCard label="Mean confidence" value={fixed(result.mean_confidence, 3)} icon={Gauge} delta={`peak probability ${fixed(result.max_probability, 3)}`} />
              </Stagger>
              <div className="grid grid-3">
                {result.max_extent_mm !== undefined && <StatCard label="Max extent" value={`${num(result.max_extent_mm, 1)} mm`} icon={Crosshair} tone="info" />}
                {result.ground_truth && (
                  <StatCard label="Dice vs expert mask" value={fixed(result.ground_truth.dice, 3)} icon={Layers} tone="info" delta={`IoU ${fixed(result.ground_truth.iou, 3)}`} />
                )}
                <StatCard label="Model test Dice" value={fixed(result.model_test_dice, 3)} icon={Gauge} tone="info" delta="held-out slices" />
              </div>
              <div className="row">
                <Badge tone="info">Image {result.image_size?.join(' × ')} px</Badge>
                <Badge>Spacing {result.pixel_spacing_mm} mm/px</Badge>
                {result.analysis_id && <Badge tone="safe">Saved to history #{result.analysis_id}</Badge>}
              </div>
              <ReportCard report={result.report} />
            </FadeIn>
          )}
        </div>
      </div>
    </div>
  )
}

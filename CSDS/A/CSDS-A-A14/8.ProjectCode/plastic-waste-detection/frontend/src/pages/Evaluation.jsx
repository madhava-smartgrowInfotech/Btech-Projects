import { useCallback, useEffect, useState } from 'react'
import { ChartLine, Crosshair, FlaskConical, Gauge, Image as ImageIcon, RefreshCw, Target, ZoomIn } from 'lucide-react'
import { Button, Card, EmptyState, ErrorState, Modal, PageHeader, PageSkeleton, StatCard } from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'

export default function Evaluation() {
  const [state, setState] = useState({ status: 'loading', data: null, error: null })
  const [zoom, setZoom] = useState(null)

  const load = useCallback(async () => {
    setState((s) => ({ ...s, status: 'loading', error: null }))
    try {
      setState({ status: 'ready', data: await api.evaluation(), error: null })
    } catch (error) {
      setState({ status: 'error', data: null, error })
    }
  }, [])

  useEffect(() => {
    document.title = 'Evaluation · PlastiScan'
    load()
  }, [load])

  const { data } = state
  const m = data?.metrics

  return (
    <div>
      <PageHeader
        eyebrow="Evaluation"
        icon={ChartLine}
        title="How well does the model detect?"
        lead="Precision, recall and mAP computed by evaluate.py from your trained model - never estimated or filled in."
        actions={
          <Button variant="secondary" icon={RefreshCw} onClick={load} loading={state.status === 'loading'}>
            Refresh
          </Button>
        }
      />

      {state.status === 'loading' && <PageSkeleton kpis={4} blocks={2} />}

      {state.status === 'error' && <ErrorState title="Could not load the evaluation results" error={state.error} onRetry={load} />}

      {state.status === 'ready' && !data.available && (
        <EmptyState
          icon={FlaskConical}
          tone="peach"
          title="No evaluation results yet"
          message="Metrics appear here after you train a model and evaluate it on the validation or test set. No values are shown until a real evaluation has been run."
          action={
            <div className="stack" style={{ '--gap': '10px', alignItems: 'center' }}>
              <span className="small">
                1. Train: <code className="cmd">python train.py --epochs 50</code>
              </span>
              <span className="small">
                2. Evaluate: <code className="cmd">python evaluate.py</code>
              </span>
              <Button variant="secondary" icon={RefreshCw} onClick={load}>
                Check again
              </Button>
            </div>
          }
        />
      )}

      {state.status === 'ready' && data.available && (
        <Stagger className="stack" gap={0.07}>
          <Stagger.Item className="grid-kpi">
            <StatCard label="Precision" display={m.precision.toFixed(3)} icon={Crosshair} tone="lavender" foot="mean across classes" />
            <StatCard label="Recall" display={m.recall.toFixed(3)} icon={Gauge} tone="mint" foot="mean across classes" />
            <StatCard label="mAP@0.5" display={m.map50.toFixed(3)} icon={Target} tone="peach" foot="IoU 0.5" />
            <StatCard label="mAP@0.5:0.95" display={m.map50_95.toFixed(3)} icon={ChartLine} tone="sky" foot="IoU 0.5 to 0.95" />
          </Stagger.Item>

          <Stagger.Item>
            <Card title="Evaluation plots" subtitle="Click a plot to enlarge it" hover={false}>
              {data.plots.length === 0 ? (
                <EmptyState
                  icon={ImageIcon}
                  tone="sky"
                  compact
                  title="No plots found in results/"
                  message="Metric plots are generated automatically by train.py and evaluate.py after a real training run."
                />
              ) : (
                <div className="plot-grid">
                  {data.plots.map((p) => (
                    <figure key={p.key} style={{ margin: 0 }}>
                      <button type="button" className="plot-btn" onClick={() => setZoom(p)} aria-label={`Enlarge ${p.label}`}>
                        <img src={p.url} alt={p.label} loading="lazy" />
                      </button>
                      <figcaption className="row between" style={{ marginTop: 8 }}>
                        <strong>{p.label}</strong>
                        <ZoomIn size={16} aria-hidden="true" className="muted" />
                      </figcaption>
                    </figure>
                  ))}
                </div>
              )}
            </Card>
          </Stagger.Item>
        </Stagger>
      )}

      <Modal open={!!zoom} onClose={() => setZoom(null)} title={zoom?.label || ''}>
        {zoom && <img className="plot-zoom" src={zoom.url} alt={zoom.label} />}
      </Modal>
    </div>
  )
}

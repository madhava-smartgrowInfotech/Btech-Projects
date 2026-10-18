import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Download, FileSearch, Printer, ScanLine, Trash2 } from 'lucide-react'
import {
  Alert,
  Breadcrumbs,
  Button,
  Card,
  ClassBadge,
  ErrorState,
  KeyValueList,
  Modal,
  PageHeader,
  ProgressBar,
  Skeleton,
  Tabs,
  useToast,
} from '../components/ui'
import { api } from '../lib/api'
import { fmtDateTime, fmtPct } from '../lib/format'
import { useAsync, useDocumentTitle } from '../lib/hooks'

const BAR = { Normal: '', 'Bacterial Pneumonia': 'coral', 'Viral Pneumonia': 'amber' }

function Xray({ src, caption, alt }) {
  const [state, setState] = useState('loading')
  return (
    <figure className="xray" style={{ margin: 0 }}>
      <figcaption className="xray-cap">{caption}</figcaption>
      {state === 'loading' && <Skeleton height="100%" style={{ position: 'absolute', inset: 0 }} />}
      {state === 'error' ? (
        <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: '#faf7f0', padding: 16, textAlign: 'center' }}>
          Image file is missing on the server.
        </div>
      ) : (
        <img src={src} alt={alt} onLoad={() => setState('ok')} onError={() => setState('error')} />
      )}
    </figure>
  )
}

export default function Result() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const { data: r, error, loading, reload } = useAsync(() => api.prediction(id), [id])
  useDocumentTitle(r ? `Result #${r.id}` : 'Result')
  const [view, setView] = useState('side')
  const [blend, setBlend] = useState(60)
  const [confirm, setConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const crumbs = (
    <Breadcrumbs items={[{ label: 'History', to: '/app/history' }, { label: r ? `Scan #${r.id}` : `Scan #${id}` }]} />
  )

  const remove = async () => {
    setDeleting(true)
    try {
      await api.remove(r.id)
      toast.success(`Scan #${r.id} deleted.`)
      nav('/app/history', { replace: true })
    } catch (e) {
      setDeleting(false)
      setConfirm(false)
      toast.error(`Could not delete the scan: ${e.message}`)
    }
  }

  if (loading && !r) {
    return (
      <>
        <PageHeader title="Detection result" crumbs={crumbs} />
        <div className="grid grid-2" role="status" aria-label="Loading result">
          <Skeleton height={420} />
          <Skeleton height={420} />
        </div>
      </>
    )
  }

  if (error) {
    const missing = error.status === 404
    return (
      <>
        <PageHeader title="Detection result" crumbs={crumbs} />
        <ErrorState
          title={missing ? 'Prediction not found' : 'Could not load this result'}
          error={error}
          hint={missing ? 'It may have been deleted. Open History to pick another scan.' : undefined}
          onRetry={missing ? undefined : reload}
        />
        {missing && (
          <div style={{ marginTop: 16 }}>
            <Button variant="primary" to="/app/history">
              Go to history
            </Button>
          </div>
        )}
      </>
    )
  }

  return (
    <>
      <PageHeader
        eyebrow={`Scan #${r.id}`}
        title="Detection result"
        crumbs={crumbs}
        actions={
          <>
            <Button variant="primary" icon={ScanLine} to="/app/detect">
              Analyze another image
            </Button>
            <Button icon={Printer} className="no-print" onClick={() => window.print()}>
              Print report
            </Button>
          </>
        }
      />

      {r.demo_mode && (
        <div style={{ marginBottom: 24 }}>
          <Alert tone="warning">
            <strong>Demo mode result.</strong> This prediction comes from an untrained network. Train the model for meaningful output.
          </Alert>
        </div>
      )}

      <div className="stack" style={{ '--gap': '24px' }}>
        <div className="no-print">
          <Tabs
            label="Image view"
            value={view}
            onChange={setView}
            tabs={[
              { id: 'side', label: 'Side by side' },
              { id: 'blend', label: 'Blend heatmap' },
            ]}
          />
        </div>

        {view === 'side' ? (
          <div className="grid grid-2">
            <Xray src={r.original_url} caption="Original X-ray" alt={`Original chest X-ray ${r.filename}`} />
            <Xray src={r.heatmap_url} caption="Grad-CAM heatmap" alt="Grad-CAM heatmap showing the regions that drove the prediction" />
          </div>
        ) : (
          <div className="stack" style={{ maxWidth: 560 }}>
            <div className="xray">
              <img src={r.original_url} alt={`Original chest X-ray ${r.filename}`} />
              <img src={r.heatmap_url} alt="" aria-hidden="true" style={{ opacity: blend / 100 }} />
              <span className="xray-cap">Heatmap {blend}%</span>
            </div>
            <label className="stack" style={{ '--gap': '4px' }}>
              <span className="field-label">Heatmap strength</span>
              <input className="range" type="range" min="0" max="100" value={blend} onChange={(e) => setBlend(Number(e.target.value))} aria-valuetext={`${blend} percent`} />
            </label>
          </div>
        )}

        <div className="grid grid-2">
          <Card title="Prediction" tone="lime">
            <div className="result-verdict">
              <span className="tiny mono">MOST LIKELY CLASS</span>
              <div>
                <ClassBadge label={r.prediction} />
              </div>
              <span className="display-md">{r.prediction}</span>
              <p>
                Confidence: <strong>{fmtPct(r.confidence, 2)}</strong>
              </p>
            </div>
          </Card>

          <Card title="Class probabilities">
            <div className="stack">
              {Object.entries(r.probabilities).map(([name, p]) => (
                <div key={name} className="prob-row">
                  <div className="row-between">
                    <span>{name}</span>
                    <span className="mono">{fmtPct(p)}</span>
                  </div>
                  <ProgressBar value={p} label={`${name} probability`} tone={BAR[name]} />
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Scan details">
          <KeyValueList
            items={[
              { label: 'File', value: r.filename },
              { label: 'Scan ID', value: `#${r.id}` },
              { label: 'Analyzed', value: fmtDateTime(r.created_at) },
              { label: 'Model', value: r.demo_mode ? 'Demo (untrained)' : 'Trained' },
            ]}
          />
          <div className="row no-print" style={{ marginTop: 16 }}>
            <Button icon={Download} href={r.heatmap_url} download={`scan-${r.id}-heatmap.png`}>
              Download heatmap
            </Button>
            <Button icon={FileSearch} to="/app/history">
              Back to history
            </Button>
            <Button variant="danger" icon={Trash2} onClick={() => setConfirm(true)}>
              Delete scan
            </Button>
          </div>
        </Card>

      </div>

      <Modal
        open={confirm}
        onClose={() => !deleting && setConfirm(false)}
        title={`Delete scan #${r.id}?`}
        footer={
          <>
            <Button onClick={() => setConfirm(false)} disabled={deleting}>
              Keep it
            </Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={remove} data-autofocus>
              Delete permanently
            </Button>
          </>
        }
      >
        <p>This removes the record, the uploaded X-ray and its heatmap. It cannot be undone.</p>
      </Modal>
    </>
  )
}

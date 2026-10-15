import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ScanLine } from 'lucide-react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Badge, Breadcrumbs, Button, Card, EmptyState, ErrorState, SkeletonBlock } from '../components/ui/index.js'
import AuthImage from '../components/AuthImage.jsx'
import { ModalityBadge, SeverityBadge } from '../components/Badges.jsx'
import { failure, fmtDate, pct } from '../lib/product.js'

export default function PatientDetail() {
  const { id } = useParams()
  const [p, setP] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    setError(null)
    setP(null)
    api
      .get(`/patients/${id}`)
      .then((r) => setP(r.data))
      .catch(async (e) => setError(await failure(e)))
  }
  useEffect(load, [id])

  if (error) {
    return (
      <ErrorState
        title="This patient could not be opened"
        error={error.message}
        hint={error.status === 404 ? 'The record may have been removed. Go back to the patient list.' : undefined}
        onRetry={load}
      />
    )
  }
  if (!p) return <SkeletonBlock rows={4} label="Loading patient" />

  return (
    <div className="page">
      <PageHeader
        crumbs={<Breadcrumbs items={[{ to: '/patients', label: 'Patients' }, { label: p.code }]} />}
        eyebrow="Patient record"
        title={p.name}
        description={`${p.code} · ${p.age} years · ${p.sex}${p.phone ? ` · ${p.phone}` : ''} · registered ${fmtDate(p.created_at)}`}
        actions={
          <Button variant="primary" icon={ScanLine} to={`/scan?patient=${p.id}`}>
            New scan
          </Button>
        }
      />

      <section className="stack" style={{ '--gap': '16px' }} aria-labelledby="history-title">
        <h2 id="history-title" className="display-sm">
          Scan history ({p.scans.length})
        </h2>
        {p.scans.length === 0 ? (
          <EmptyState title="No scans yet" action={<Button variant="primary" icon={ScanLine} to={`/scan?patient=${p.id}`}>Upload the first scan</Button>}>
            This patient has no scans. Upload a chest X-ray or CT slice to start a screening.
          </EmptyState>
        ) : (
          <div className="grid grid-4" style={{ '--gap': '16px' }}>
            {p.scans.map((s) => (
              <Link key={s.id} to={`/scans/${s.id}`} className="card card-interactive scan-thumb">
                <AuthImage src={`/scans/${s.id}/image/heatmap`} alt={`Heatmap for scan ${s.id}`} />
                <div className="row" style={{ '--gap': '6px' }}>
                  <ModalityBadge value={s.modality} />
                  <SeverityBadge value={s.severity} />
                </div>
                <p>
                  <strong>{s.prediction}</strong> <Badge>{pct(s.confidence)}</Badge>
                </p>
                <p className="tiny muted">Scan #{s.id} · {fmtDate(s.created_at)}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

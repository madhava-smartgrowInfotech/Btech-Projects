import { Card, CardHeader, Badge, KeyValueList } from '../ui/display'
import { ErrorState, Skeleton } from '../ui/feedback'

// Square frame for an MRI image / overlay with a placeholder or skeleton.
export function Figure({ title, src, placeholder = 'No image selected', loading, alt }) {
  return (
    <figure className="figure">
      <figcaption className="field-label">{title}</figcaption>
      <div className="figure-frame">
        {loading ? (
          <Skeleton width="100%" height="100%" radius={0} />
        ) : src ? (
          <img src={src} alt={alt || title} />
        ) : (
          <span className="figure-empty">{placeholder}</span>
        )}
      </div>
    </figure>
  )
}

// Horizontal probability bars for classifier outputs (values 0-1).
export function ProbBars({ probs, best }) {
  return (
    <ul className="probs" aria-label="Class probabilities">
      {Object.entries(probs).map(([k, v]) => (
        <li key={k} className={k === best ? 'best' : ''}>
          <span className="probs-name">{k}</span>
          <span className="probs-track" aria-hidden="true">
            <i style={{ width: `${Math.max(0, Math.min(1, v)) * 100}%` }} />
          </span>
          <span className="probs-val">{(v * 100).toFixed(1)}%</span>
        </li>
      ))}
    </ul>
  )
}

function BulletList({ title, items }) {
  if (!items?.length) return null
  return (
    <section>
      <h4 className="report-h">{title}</h4>
      <ul className="report-list">
        {items.map((f, i) => (
          <li key={i}>{f}</li>
        ))}
      </ul>
    </section>
  )
}

// Structured Gemini report (or the clearly labelled plain-summary fallback).
export function ReportCard({ report }) {
  if (!report?.report) return null
  const r = report.report
  const fallback = report.source !== 'gemini'
  return (
    <Card className="report" aria-label="Structured report">
      <CardHeader
        title="Structured report"
        subtitle={
          fallback
            ? 'The AI report service was unreachable - this is a plain summary of the model output.'
            : `Written by ${report.model} from the model output`
        }
        actions={
          <Badge tone={fallback ? 'warn' : 'info'} dot>
            {fallback ? 'Plain summary' : 'Gemini'}
          </Badge>
        }
      />
      <div className="card-body stack" style={{ gap: 16 }}>
        {r.title && <h3 className="report-title">{r.title}</h3>}
        {r.summary && <p>{r.summary}</p>}
        <BulletList title="Findings" items={r.findings} />
        {r.measurements?.length > 0 && (
          <section>
            <h4 className="report-h">Measurements</h4>
            <KeyValueList items={r.measurements.map((m) => [m.name, m.value])} />
          </section>
        )}
        {r.interpretation && (
          <section>
            <h4 className="report-h">Interpretation</h4>
            <p className="muted">{r.interpretation}</p>
          </section>
        )}
        <BulletList title="Limitations" items={r.limitations} />
        {r.recommendation && <p className="report-reco">{r.recommendation}</p>}
      </div>
    </Card>
  )
}

// Skeleton shown while a route chunk loads.
export function PageSkeleton() {
  return (
    <div className="container" aria-busy="true" aria-label="Loading page">
      <Skeleton width={180} height={14} />
      <Skeleton width="45%" height={34} style={{ margin: '14px 0 28px' }} />
      <div className="grid grid-4">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={128} radius={12} />
        ))}
      </div>
      <Skeleton height={320} radius={12} style={{ marginTop: 18 }} />
    </div>
  )
}

export function CardSkeleton({ rows = 4 }) {
  return (
    <div className="card-body" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} height={20} style={{ margin: '12px 0' }} />
      ))}
    </div>
  )
}

// A data call failed: say what failed and what to do.
export function LoadError({ title, error, onRetry, hint }) {
  const offline = error?.status === 0
  return (
    <Card>
      <ErrorState title={title} error={error} onRetry={onRetry}>
        <p className="faint">{hint || (offline ? 'Start the backend with run.bat, then try again.' : 'Try again, or sign in again if your session expired.')}</p>
      </ErrorState>
    </Card>
  )
}

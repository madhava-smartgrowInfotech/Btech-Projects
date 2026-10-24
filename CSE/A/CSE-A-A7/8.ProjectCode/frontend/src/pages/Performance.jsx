import { Suspense, lazy, useCallback, useEffect, useState } from 'react'
import { BarChart3, Clock, Gauge, Target, Users } from 'lucide-react'
import { Alert, Button, Card, EmptyState, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'
import { PriorityBlock } from '../components/athena/bits'
import { api } from '../lib/api'
import { fmtPct, PRIORITY_COLOR, PRIORITY_NAME } from '../lib/format'

const BarBlocks = lazy(() => import('../components/ui/Charts').then((m) => ({ default: m.BarBlocks })))
const chartFallback = <Skeleton height={280} />

function Confusion({ matrix }) {
  const max = Math.max(...matrix.flat(), 1)
  return (
    <div className="confusion-wrap" data-lenis-prevent>
      <table className="confusion">
        <caption className="sr-only">Confusion matrix: rows are recorded priority, columns are model priority</caption>
        <thead>
          <tr>
            <th scope="col">Recorded ↓ / Model →</th>
            {[1, 2, 3, 4, 5].map((n) => (
              <th scope="col" key={n}>P{n}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <th scope="row">P{i + 1}</th>
              {row.map((v, j) => (
                <td key={j} className={i === j ? 'hit' : ''} style={{ background: v ? `color-mix(in srgb, var(--lime) ${Math.round((v / max) * 100)}%, var(--surface))` : 'var(--surface)', color: 'var(--ink)' }}>
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Performance() {
  const [state, setState] = useState({ loading: true, data: null, error: null })
  const load = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .metrics()
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }))
  }, [])
  useEffect(load, [load])

  if (state.loading && !state.data)
    return (
      <>
        <PageHeader eyebrow="Evaluation" title="Model performance" />
        <div className="grid grid-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={150} />)}</div>
      </>
    )
  if (state.error) return <ErrorState title="Could not load the metrics" error={state.error} onRetry={load} />

  const { offline: o, live: l } = state.data
  if (!o)
    return (
      <EmptyState icon={BarChart3} title="No evaluation yet" action={<Button variant="primary" onClick={load}>Check again</Button>}>
        Train the model with <code>python ml/train.py</code> to create experiments/metrics.json.
      </EmptyState>
    )

  const recall = Object.entries(o.per_class_recall).map(([k, v]) => ({ priority: `P${k}`, recall: Math.round(v * 1000) / 10, color: PRIORITY_COLOR[k] }))
  const dist = Object.entries(l.priority_distribution).map(([k, v]) => ({ priority: `P${k}`, patients: v, color: PRIORITY_COLOR[k] }))

  return (
    <>
      <PageHeader
        eyebrow="Evaluation"
        title="Model performance"
        description="How closely the triage model matches the recorded priority, and how fast it works."
      />
      <div className="stack" style={{ '--gap': '24px' }}>
        <Alert tone="info">
          Evaluated on {o.n_test.toLocaleString()} held-out cases from a seeded <strong>synthetic</strong> dataset (see docs). Real hospital data will give different numbers.
        </Alert>
        <Stagger className="grid grid-4" inView={false}>
          <StatCard label="Accuracy" value={Math.round(o.accuracy * 1000) / 10} decimals={1} icon={Target} hint="exact priority match" tone="lime" />
          <StatCard label="Within one level" value={Math.round(o.within_one_priority * 1000) / 10} decimals={1} icon={Gauge} hint="off by at most one priority" />
          <StatCard label="Macro F1" value={Math.round(o.macro_f1 * 1000) / 1000} decimals={3} icon={BarChart3} hint="mean over the 5 priorities" />
          <StatCard label="Seconds per patient" value={l.mean_seconds_per_patient ?? '—'} decimals={2} icon={Clock} hint={l.mean_seconds_per_patient ? `live average, report reading included · model alone ${(o.model_seconds_per_patient * 1000).toFixed(3)} ms` : `model alone ${(o.model_seconds_per_patient * 1000).toFixed(3)} ms · no live patients yet`} />
        </Stagger>

        <div className="grid grid-2">
          <SlideUp>
            <Card title="Recall per priority">
              <p className="small muted" style={{ marginBottom: 10 }}>Of the patients recorded at each priority, the share the model placed correctly (%).</p>
              <Suspense fallback={chartFallback}>
                <BarBlocks data={recall} xKey="priority" yKey="recall" name="Recall %" colorFn={(d) => d.color} />
              </Suspense>
              <ul className="row" style={{ marginTop: 12 }}>
                {Object.entries(o.support).map(([k, v]) => (
                  <li key={k} className="row" style={{ '--gap': '6px', listStyle: 'none' }}>
                    <PriorityBlock p={Number(k)} /> <span className="tiny mono">{v} cases</span>
                  </li>
                ))}
              </ul>
            </Card>
          </SlideUp>
          <SlideUp delay={0.08}>
            <Card title="Confusion matrix">
              <p className="small muted" style={{ marginBottom: 10 }}>Counts on the held-out set. The diagonal is correct. Most misses land one level away.</p>
              <Confusion matrix={o.confusion_matrix} />
            </Card>
          </SlideUp>
        </div>

        <SlideUp>
          <Card title="In this system">
            <div className="grid grid-3" style={{ marginBottom: 20 }}>
              <StatCard label="Patients triaged" value={l.patients} icon={Users} hint={`${l.live_patients} entered live · ${l.patients - l.live_patients} sample cases`} />
              <StatCard label="Clinician reviews" value={l.reviewed} icon={Target} hint={`${l.overridden} priorities changed`} />
              <StatCard label="Clinician agreement" value={l.agreement_rate === null ? '—' : fmtPct(l.agreement_rate)} icon={Gauge} hint={l.agreement_rate === null ? 'No reviews yet' : 'reviews that kept the model priority'} />
            </div>
            {l.recorded_outcome_accuracy !== null && (
              <p className="small" style={{ marginBottom: 12 }}>
                On the {l.recorded_outcome_cases} sample cases that carry a recorded priority, the model matched it {fmtPct(l.recorded_outcome_accuracy)} of the time.
              </p>
            )}
            <Suspense fallback={chartFallback}>
              <BarBlocks data={dist} xKey="priority" yKey="patients" name="Patients" colorFn={(d) => d.color} height={220} />
            </Suspense>
            <p className="tiny muted" style={{ marginTop: 8 }}>
              {Object.keys(PRIORITY_NAME).map((k) => `P${k} ${PRIORITY_NAME[k]}`).join(' · ')}
            </p>
          </Card>
        </SlideUp>
      </div>
    </>
  )
}

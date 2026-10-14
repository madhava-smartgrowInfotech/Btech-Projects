import { RefreshCw } from 'lucide-react'
import useFetch from '../lib/useFetch'
import { num, pct } from '../lib/hospi'
import { PageHeader } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Badge, Card, StatCard } from '../components/ui/Display'
import { Alert, ErrorState, SkeletonBlock } from '../components/ui/Feedback'
import { Table } from '../components/ui/Table'
import { BarBlocks, PALETTE } from '../components/ui/Charts'

function BarRow({ label, value, max, valueLabel, tone = 'var(--lime)' }) {
  const width = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <li className="bar-row">
      <span className="bar-label" title={label}>
        {label}
      </span>
      <span className="bar-track" aria-hidden="true">
        <span className="bar-fill" style={{ width: `${width}%`, background: tone }} />
      </span>
      <span className="bar-value">{valueLabel}</span>
    </li>
  )
}

export default function Performance() {
  const { data, error, loading, reload } = useFetch('/metrics')

  const header = (
    <PageHeader
      eyebrow="Model"
      title="Model performance"
      description="Held-out evaluation: October to December admissions, never used in training."
      actions={
        <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
          Refresh
        </Button>
      }
    />
  )

  if (loading && !data) {
    return (
      <>
        {header}
        <SkeletonBlock rows={8} label="Loading model performance" />
      </>
    )
  }
  if (!data) {
    return (
      <>
        {header}
        <ErrorState title="Model performance could not load" error={error} onRetry={reload} />
      </>
    )
  }

  const ev = data.evaluation
  const tr = data.training
  const los = ev?.length_of_stay
  const cf = ev?.census_forecast
  const ru = ev?.resource_use
  const maxImp = Math.max(...data.feature_importance.map((f) => f.importance))

  return (
    <>
      {header}
      {error && (
        <div style={{ marginBottom: 20 }}>
          <ErrorState title="Showing the last loaded results" error={error} onRetry={reload} />
        </div>
      )}
      {!ev && <Alert tone="error">Evaluation results not found. Run ml\eval.py to produce them.</Alert>}

      <h2 className="display-sm" style={{ margin: '8px 0 16px' }}>
        Length of stay
      </h2>
      <div className="grid grid-4" style={{ '--gap': '16px', marginBottom: 20 }}>
        <StatCard
          label="Mean absolute error"
          value={`${num(los?.mae_days ?? tr.length_of_stay.regression.mae_days)} d`}
          hint={`Predicting the average gives ${num(los?.baseline_mean_mae_days ?? tr.length_of_stay.regression.baseline_mean_mae_days)} d`}
          tone="lime"
        />
        <StatCard label="R²" value={num(los?.r2 ?? tr.length_of_stay.regression.r2)} hint={`RMSE ${num(los?.rmse_days ?? tr.length_of_stay.regression.rmse_days)} d`} />
        <StatCard
          label="Within 1 day"
          value={los ? pct(los.within_1_day, 1) : '—'}
          hint={`${los?.test_patients?.toLocaleString() ?? ''} test patients`}
        />
        <StatCard
          label="Long-stay F1 / AUC"
          value={`${num(los?.long_stay_f1 ?? tr.length_of_stay.classification.f1)} / ${num(los?.long_stay_auc ?? tr.length_of_stay.classification.roc_auc)}`}
          hint={`Accuracy ${pct(los?.long_stay_accuracy ?? tr.length_of_stay.classification.accuracy, 1)}`}
        />
      </div>

      <div className="grid grid-2" style={{ '--gap': '24px', marginBottom: 36 }}>
        <Card title="What drives the length-of-stay model">
          <p className="tiny muted" style={{ marginBottom: 14 }}>
            XGBoost gain, share of the model&apos;s learning.
          </p>
          <ul className="bar-list" aria-label="Feature importance">
            {data.feature_importance.map((f) => (
              <BarRow key={f.feature} label={f.label} value={f.importance} max={maxImp} valueLabel={pct(f.importance, 1)} />
            ))}
          </ul>
        </Card>
        {los ? (
          <Card title="Error by ward (MAE, days)">
            <BarBlocks
              data={Object.entries(los.mae_by_ward).map(([ward, mae]) => ({ ward, mae }))}
              xKey="ward"
              yKey="mae"
              name="MAE (days)"
              color={PALETTE.sky}
              height={240}
            />
            <p className="tiny muted" style={{ marginTop: 14 }}>
              Admissions forecast, next 14 days per facility and ward: MAE {num(tr.admissions.mae)}, against {num(tr.admissions.naive_7d_mean_mae)} for a
              7-day average and {num(tr.admissions.naive_last_day_mae)} for &quot;same as yesterday&quot;.
            </p>
          </Card>
        ) : (
          <Card title="Error by ward">
            <Alert tone="warning">Ward errors need the evaluation results.</Alert>
          </Card>
        )}
      </div>

      {cf && (
        <>
          <h2 className="display-sm" style={{ margin: '8px 0 16px' }}>
            Occupancy forecast, rolling back-tests
          </h2>
          <div className="grid grid-4" style={{ '--gap': '16px', marginBottom: 24 }}>
            <StatCard label="MAE, beds per ward" value={num(cf.mae_overall.model)} hint={`${cf.origins} forecast dates × ${cf.series} wards × ${cf.horizon_days} days`} tone="lime" />
            <StatCard label="Versus persistence" value={pct(cf.improvement_vs_persistence, 1)} hint={`Lower error than "no change" (${num(cf.mae_overall.persistence)})`} />
            <StatCard label="Versus 28-day average" value={pct(cf.improvement_vs_mean_28d, 1)} hint={`Lower error than the recent mean (${num(cf.mae_overall.mean_28d)})`} />
            <StatCard label="90% band coverage" value={pct(cf.band_90_coverage, 1)} hint="Share of actual values inside the band" />
          </div>

          <div className="grid grid-2" style={{ '--gap': '24px', marginBottom: 36 }}>
            <Card title="MAE by forecast horizon" className="table-scroll-x">
              <Table
                caption="Forecast error by horizon for HospiSense, persistence and the 28-day average"
                rows={Object.entries(cf.mae_by_horizon).map(([h, v]) => ({ h: Number(h), ...v }))}
                rowKey={(r) => r.h}
                initialSort={{ key: 'h', dir: 'asc' }}
                columns={[
                  { key: 'h', label: 'Horizon', render: (r) => `Day ${r.h}`, numeric: false },
                  { key: 'model', label: 'HospiSense', numeric: true, render: (r) => <strong>{num(r.model)}</strong> },
                  { key: 'persistence', label: 'Persistence', numeric: true, render: (r) => num(r.persistence) },
                  { key: 'mean_28d', label: '28-day average', numeric: true, render: (r) => num(r.mean_28d) },
                ]}
              />
            </Card>
            <Card title="ICU alerts against what happened (next 7 days)" className="table-scroll-x">
              <Table
                caption="ICU alert hits, misses and false alarms"
                rows={[
                  { key: 'early_warning', label: 'Early warning', ...cf.icu_alerts.early_warning },
                  { key: 'over_capacity', label: 'Over capacity (expected)', ...cf.icu_alerts.over_capacity },
                ]}
                rowKey={(r) => r.key}
                columns={[
                  { key: 'label', label: 'Alert' },
                  { key: 'tp', label: 'Caught', numeric: true },
                  { key: 'fn', label: 'Missed', numeric: true },
                  { key: 'fp', label: 'False alarms', numeric: true },
                  { key: 'recall', label: 'Recall', numeric: true, render: (r) => <strong>{pct(r.recall)}</strong> },
                  { key: 'precision', label: 'Precision', numeric: true, render: (r) => pct(r.precision) },
                ]}
              />
              <p className="tiny muted" style={{ marginTop: 12 }}>
                The early warning is tuned to catch most ICU overruns, and accepts some false alarms in return.
              </p>
            </Card>
          </div>
        </>
      )}

      {ru && (
        <>
          <h2 className="display-sm" style={{ margin: '8px 0 16px' }}>
            Optimised plan against the current allocation
          </h2>
          <Card className="table-scroll-x" style={{ marginBottom: 12 }}>
            <Table
              caption="Resource use under the static allocation and the HospiSense plan"
              rows={[
                { key: 'patient_days_without_bed', label: 'Patient-days without a bed' },
                { key: 'nurse_shifts_short', label: 'Nurse shifts short of safe ratio' },
                { key: 'equipment_unit_days_short', label: 'Equipment unit-days short' },
                { key: 'nurse_shifts_idle', label: 'Nurse shifts above need' },
                { key: 'nurse_shifts_rostered', label: 'Nurse shifts rostered' },
              ].map((r) => {
                const a = ru.static[r.key]
                const b = ru.optimised[r.key]
                const change = a ? (b - a) / a : 0
                const good = r.key === 'nurse_shifts_rostered' || r.key === 'nurse_shifts_idle' ? change <= 0 : change < 0
                return { ...r, a, b, change, good }
              })}
              rowKey={(r) => r.key}
              columns={[
                { key: 'label', label: 'Measured on the census that actually happened' },
                { key: 'a', label: 'Static allocation', numeric: true, render: (r) => r.a.toLocaleString() },
                { key: 'b', label: 'HospiSense plan', numeric: true, render: (r) => r.b.toLocaleString() },
                {
                  key: 'change',
                  label: 'Change',
                  numeric: true,
                  render: (r) => (
                    <Badge tone={r.good ? 'pass' : 'closed'}>
                      {r.change > 0 ? '+' : ''}
                      {pct(r.change, 1)}
                    </Badge>
                  ),
                },
              ]}
            />
          </Card>
          <p className="tiny muted">
            {ru.plans} plans (one per back-test date), each scored over the following {ru.days_scored_per_plan} days. Plans cover the expected 7-day peak,
            so shortages fall at the cost of more rostered shifts on quieter days. Mean solve time {ru.mean_solve_seconds} s.
          </p>
        </>
      )}
    </>
  )
}

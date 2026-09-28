import { useCallback, useEffect, useState } from 'react'
import api, { errorMessage } from '../api'
import { Badge, ErrorBox, Kpi, Loading, PageHeader, pct } from '../components/ui'

const f2 = (x) => Number(x).toFixed(2)

function Bar({ value, max, tone = 'bg-teal-600' }) {
  return (
    <div className="h-2.5 bg-slate-100 rounded w-full">
      <div className={`h-2.5 rounded ${tone}`} style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
    </div>
  )
}

export default function Performance() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/metrics')
      setData(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => {
    load()
  }, [load])

  if (loading) return <Loading label="Loading model performance..." />
  if (!data) return <ErrorBox message={error} onRetry={load} />
  const ev = data.evaluation
  const tr = data.training
  const los = ev?.length_of_stay
  const cf = ev?.census_forecast
  const ru = ev?.resource_use
  const maxImp = Math.max(...data.feature_importance.map((f) => f.importance))

  return (
    <div>
      <PageHeader title="Model performance" subtitle="Held-out evaluation: October-December admissions, never used in training" />
      {!ev && <ErrorBox message="Evaluation results not found - run: venv\Scripts\python ml\eval.py" />}

      <h2 className="font-semibold text-slate-900 mb-3">Length of stay</h2>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <Kpi label="MAE" value={`${f2(los?.mae_days ?? tr.length_of_stay.regression.mae_days)} d`} sub={`vs ${f2(los?.baseline_mean_mae_days ?? tr.length_of_stay.regression.baseline_mean_mae_days)} d predicting the average`} tone="teal" />
        <Kpi label="R2" value={f2(los?.r2 ?? tr.length_of_stay.regression.r2)} sub={`RMSE ${f2(los?.rmse_days ?? tr.length_of_stay.regression.rmse_days)} d`} />
        <Kpi label="Within 1 day" value={los ? pct(los.within_1_day, 1) : '-'} sub={`${los?.test_patients?.toLocaleString() ?? ''} test patients`} />
        <Kpi label="Long-stay F1 / AUC" value={`${f2(los?.long_stay_f1 ?? tr.length_of_stay.classification.f1)} / ${f2(los?.long_stay_auc ?? tr.length_of_stay.classification.roc_auc)}`} sub={`accuracy ${pct(los?.long_stay_accuracy ?? tr.length_of_stay.classification.accuracy, 1)}`} />
      </div>
      <div className="grid lg:grid-cols-2 gap-4 mb-8">
        <div className="card p-4">
          <h3 className="font-medium text-slate-900 mb-3">What drives the length-of-stay model (XGBoost gain)</h3>
          <ul className="space-y-2">
            {data.feature_importance.map((f) => (
              <li key={f.feature} className="grid grid-cols-[180px_1fr_50px] items-center gap-2 text-sm">
                <span className="truncate text-slate-700" title={f.label}>{f.label}</span>
                <Bar value={f.importance} max={maxImp} />
                <span className="text-right text-xs text-slate-500">{pct(f.importance, 1)}</span>
              </li>
            ))}
          </ul>
        </div>
        {los && (
          <div className="card p-4">
            <h3 className="font-medium text-slate-900 mb-3">Error by ward (MAE, days)</h3>
            <ul className="space-y-2">
              {Object.entries(los.mae_by_ward).map(([w, v]) => (
                <li key={w} className="grid grid-cols-[110px_1fr_50px] items-center gap-2 text-sm">
                  <span className="text-slate-700">{w}</span>
                  <Bar value={v} max={Math.max(...Object.values(los.mae_by_ward))} tone="bg-sky-600" />
                  <span className="text-right text-xs text-slate-500">{f2(v)}</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-slate-500 mt-4">
              Admissions forecast (next 14 days, per facility and ward): MAE {f2(tr.admissions.mae)} vs {f2(tr.admissions.naive_7d_mean_mae)} for a 7-day average
              and {f2(tr.admissions.naive_last_day_mae)} for "same as yesterday".
            </p>
          </div>
        )}
      </div>

      {cf && (
        <>
          <h2 className="font-semibold text-slate-900 mb-3">Occupancy forecast (rolling back-tests)</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <Kpi label="MAE (beds per ward)" value={f2(cf.mae_overall.model)} sub={`${cf.origins} forecast dates x ${cf.series} wards x ${cf.horizon_days} days`} tone="teal" />
            <Kpi label="vs persistence" value={pct(cf.improvement_vs_persistence, 1)} sub={`lower error than "no change" (${f2(cf.mae_overall.persistence)})`} tone="teal" />
            <Kpi label="vs 28-day average" value={pct(cf.improvement_vs_mean_28d, 1)} sub={`lower error than the recent mean (${f2(cf.mae_overall.mean_28d)})`} tone="teal" />
            <Kpi label="90% band coverage" value={pct(cf.band_90_coverage, 1)} sub="share of actual values inside the band" />
          </div>
          <div className="grid lg:grid-cols-2 gap-4 mb-8">
            <div className="card overflow-x-auto">
              <h3 className="font-medium text-slate-900 px-4 pt-4 pb-2">MAE by forecast horizon</h3>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th">Horizon</th>
                    <th className="th">HospiSense</th>
                    <th className="th">Persistence</th>
                    <th className="th">28-day average</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(cf.mae_by_horizon).map(([h, v]) => (
                    <tr key={h}>
                      <td className="td">Day {h}</td>
                      <td className="td font-semibold text-teal-800">{f2(v.model)}</td>
                      <td className="td">{f2(v.persistence)}</td>
                      <td className="td">{f2(v.mean_28d)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="card overflow-x-auto">
              <h3 className="font-medium text-slate-900 px-4 pt-4 pb-2">ICU alerts vs what happened (next 7 days)</h3>
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="th">Alert</th>
                    <th className="th">Caught</th>
                    <th className="th">Missed</th>
                    <th className="th">False alarms</th>
                    <th className="th">Recall</th>
                    <th className="th">Precision</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['early_warning', 'Early warning'],
                    ['over_capacity', 'Over capacity (expected)'],
                  ].map(([k, label]) => {
                    const c = cf.icu_alerts[k]
                    return (
                      <tr key={k}>
                        <td className="td">{label}</td>
                        <td className="td">{c.tp}</td>
                        <td className="td">{c.fn}</td>
                        <td className="td">{c.fp}</td>
                        <td className="td font-semibold">{pct(c.recall)}</td>
                        <td className="td">{pct(c.precision)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <p className="text-xs text-slate-500 px-4 py-3">The early warning is tuned to catch most ICU overruns; it accepts some false alarms in return.</p>
            </div>
          </div>
        </>
      )}

      {ru && (
        <>
          <h2 className="font-semibold text-slate-900 mb-3">Resource use: optimised plan vs current (static) allocation</h2>
          <div className="card overflow-x-auto mb-4">
            <table className="w-full min-w-[560px]">
              <thead>
                <tr>
                  <th className="th">Measured on the census that actually happened</th>
                  <th className="th">Static allocation</th>
                  <th className="th">HospiSense plan</th>
                  <th className="th">Change</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['patient_days_without_bed', 'Patient-days without a bed'],
                  ['nurse_shifts_short', 'Nurse shifts short of safe ratio'],
                  ['equipment_unit_days_short', 'Equipment unit-days short'],
                  ['nurse_shifts_idle', 'Nurse shifts above need'],
                  ['nurse_shifts_rostered', 'Nurse shifts rostered'],
                ].map(([k, label]) => {
                  const a = ru.static[k]
                  const b = ru.optimised[k]
                  const change = a ? (b - a) / a : 0
                  const good = k === 'nurse_shifts_rostered' || k === 'nurse_shifts_idle' ? change <= 0 : change < 0
                  return (
                    <tr key={k}>
                      <td className="td">{label}</td>
                      <td className="td">{a.toLocaleString()}</td>
                      <td className="td">{b.toLocaleString()}</td>
                      <td className="td">
                        <Badge tone={good ? 'teal' : 'amber'}>
                          {change > 0 ? '+' : ''}
                          {pct(change, 1)}
                        </Badge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <p className="text-xs text-slate-500 px-4 py-3">
              {ru.plans} plans (one per back-test date), each scored over the following {ru.days_scored_per_plan} days. Plans cover the expected 7-day peak, so shortages
              fall at the cost of more rostered shifts on quieter days. Mean solve time {ru.mean_solve_seconds}s.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import api, { ACTIVITY_COLORS, errMsg, label } from '../api.js'
import { ErrorBox, PageTitle, Spinner, Stat } from '../components/ui.jsx'

const pct = (v) => (v == null ? '-' : `${(v * 100).toFixed(1)}%`)
const sec = (v) => (v == null ? '-' : `${Number(v).toFixed(2)} s`)
const COND = {
  normal: 'Normal light',
  dim_no_enhancement: 'Dim, no enhancement',
  dim_enhanced: 'Dim + CareWatch enhancement',
  occluded_legs: 'Legs occluded',
}

function Confusion({ classes, matrix }) {
  const max = Math.max(1, ...matrix.flat())
  return (
    <div className="overflow-x-auto">
      <table className="text-xs">
        <thead><tr><th className="p-1 text-left text-slate-400">true \ predicted</th>{classes.map((c) => <th key={c} className="p-1 capitalize font-medium text-slate-600">{label(c)}</th>)}</tr></thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <td className="p-1 capitalize font-medium text-slate-600">{label(classes[i])}</td>
              {row.map((v, j) => (
                <td key={j} className="p-1 text-center tabular-nums w-16" style={{ background: `rgba(13,148,136,${v / max})`, color: v / max > 0.5 ? 'white' : '#334155' }}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Performance() {
  const [m, setM] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const load = async () => {
    setLoading(true); setError('')
    try { const { data } = await api.get('/metrics'); setM(data) } catch (e) { setError(errMsg(e)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (!m) return <div><ErrorBox error={error} onRetry={load} />{!error && <Spinner />}</div>
  const tr = m.training
  const ev = m.evaluation
  const act = ev?.activity
  const fall = ev?.fall
  const lat = ev?.latency

  return (
    <div className="space-y-5">
      <PageTitle title="Model performance" subtitle="Activity recognition accuracy, fall detection and alert latency">
        <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
      </PageTitle>
      <ErrorBox error={error} />
      {!tr && <div className="card p-6 text-slate-500">No trained model found - run <code>python ml/train.py</code>.</div>}
      {!ev && <div className="card p-6 text-slate-500">No evaluation yet - run <code>python ml/eval.py</code>.</div>}

      {act && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(act.conditions).map(([k, c]) => (
              <Stat key={k} label={COND[k] || k} value={pct(c.accuracy)} hint={`macro F1 ${pct(c.macro_f1)} - ${c.windows} windows`} />
            ))}
          </div>
          <div className="card p-5">
            <h2 className="font-semibold text-slate-900 mb-3">Per-activity accuracy and F1</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="py-2 pr-3">Activity</th>
                    {Object.keys(act.conditions).map((k) => <th key={k} className="py-2 pr-3" colSpan={2}>{COND[k] || k}</th>)}
                  </tr>
                  <tr className="text-left text-xs text-slate-400 border-b border-slate-100">
                    <th />
                    {Object.keys(act.conditions).map((k) => [<th key={k + 'a'} className="py-1">Acc.</th>, <th key={k + 'f'} className="py-1 pr-3">F1</th>])}
                  </tr>
                </thead>
                <tbody>
                  {act.classes.map((c) => (
                    <tr key={c} className="border-b border-slate-100">
                      <td className="py-2 pr-3 capitalize"><span className="inline-block w-2.5 h-2.5 rounded-sm mr-2" style={{ background: ACTIVITY_COLORS[c] }} />{label(c)}</td>
                      {Object.entries(act.conditions).map(([k, cond]) => [
                        <td key={k + 'a'} className="py-2 tabular-nums">{pct(cond.per_class[c]?.accuracy)}</td>,
                        <td key={k + 'f'} className="py-2 pr-3 tabular-nums">{pct(cond.per_class[c]?.f1)}</td>,
                      ])}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-slate-500 mt-3">{act.note}</p>
          </div>
        </>
      )}

      {fall && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card p-5">
            <h2 className="font-semibold text-slate-900 mb-3">Fall detection</h2>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Sensitivity" value={pct(fall.sensitivity)} hint={`${fall.tp} of ${fall.positives} falls caught`} />
              <Stat label="Specificity" value={pct(fall.specificity)} hint={`${fall.tn} of ${fall.negatives} non-falls ignored`} />
            </div>
            <table className="w-full text-sm mt-4">
              <thead><tr className="text-left text-slate-500 border-b border-slate-200"><th className="py-1.5">Scenario</th><th>Sequences</th><th>Alerts raised</th></tr></thead>
              <tbody>
                {Object.entries(fall.by_scenario).map(([k, v]) => (
                  <tr key={k} className="border-b border-slate-100">
                    <td className="py-1.5">{k.replaceAll('_', ' ')} {v.is_fall && <span className="text-xs text-red-600">(fall)</span>}</td>
                    <td className="tabular-nums">{v.n}</td><td className="tabular-nums">{v.alerts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold text-slate-900 mb-3">Alert latency</h2>
            <div className="grid grid-cols-2 gap-3">
              <Stat label="Impact to confirmed fall" value={sec(fall.detection_latency_s?.mean)} hint={`median ${sec(fall.detection_latency_s?.median)}, 95th pct ${sec(fall.detection_latency_s?.p95)}`} />
              <Stat label="Pose model per frame" value={lat ? `${lat.pose_ms_per_frame} ms` : '-'} hint={lat ? `${lat.pipeline_fps} fps on CPU` : ''} />
              <Stat label="Alert delivery" value={lat?.dispatch_ms != null ? `${lat.dispatch_ms} ms` : '-'} hint={lat?.dispatch_note} />
              <Stat label="Impact to alert sent" value={sec(lat?.end_to_end_s)} hint={`includes the ${lat?.countdown_s}s 'I'm OK' countdown`} />
            </div>
            {m.live?.fall_alerts > 0 && (
              <p className="text-sm text-slate-600 mt-4">
                Live so far: {m.live.fall_alerts} fall alerts, {m.live.sent} sent, {m.live.cancelled_im_ok} cancelled with 'I'm OK'
                {m.live.mean_detection_latency_ms != null && `, mean confirmation ${(m.live.mean_detection_latency_ms / 1000).toFixed(2)} s`}.
              </p>
            )}
          </div>
        </div>
      )}

      {tr && (
        <div className="card p-5">
          <h2 className="font-semibold text-slate-900">Training</h2>
          <p className="text-sm text-slate-600 mt-1">{tr.model} - {tr.train_windows} training windows ({tr.own_clip_train_windows} from recorded clips), trained in {tr.train_seconds}s on CPU.</p>
          <div className="mt-4"><Confusion classes={tr.classes} matrix={tr.confusion_matrix} /></div>
        </div>
      )}
    </div>
  )
}

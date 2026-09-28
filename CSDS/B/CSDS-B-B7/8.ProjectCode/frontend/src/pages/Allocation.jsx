import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowRight, CheckCircle2, Loader2, Play, RotateCcw } from 'lucide-react'
import api, { errorMessage } from '../api'
import { Badge, ErrorBox, Loading, PageHeader } from '../components/ui'

const GROUPS = [
  ['bed_conversion', 'Bed conversions'],
  ['diversion', 'Admission diversions'],
  ['nurse_float', 'Nurse floats'],
  ['extra_shift', 'Extra nurse shifts'],
  ['equipment_transfer', 'Equipment transfers'],
]

function describe(a) {
  switch (a.type) {
    case 'bed_conversion':
      return <>Facility {a.facility}: {a.from_ward} <ArrowRight size={12} className="inline" /> {a.to_ward} beds</>
    case 'diversion':
      return <>{a.ward} admissions: Facility {a.facility} <ArrowRight size={12} className="inline" /> Facility {a.to_facility}</>
    case 'nurse_float':
      return <>Facility {a.facility} {a.shift}: {a.from_ward} <ArrowRight size={12} className="inline" /> {a.to_ward} nurses</>
    case 'extra_shift':
      return <>Facility {a.facility} {a.ward}: extra {a.shift} nurses</>
    case 'equipment_transfer':
      return <>{a.item}: Facility {a.facility} <ArrowRight size={12} className="inline" /> Facility {a.to_facility}</>
    default:
      return a.type
  }
}

function Compare({ label, before, after }) {
  const better = after < before
  return (
    <div className="card p-4">
      <div className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</div>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-xl font-semibold text-slate-400 line-through decoration-1">{before}</span>
        <ArrowRight size={14} className="text-slate-400" />
        <span className={`text-2xl font-semibold ${after === 0 ? 'text-teal-700' : better ? 'text-amber-700' : 'text-red-700'}`}>{after}</span>
      </div>
      <div className="text-xs text-slate-500 mt-1">current allocation vs with plan (at forecast peak)</div>
    </div>
  )
}

export default function Allocation({ user }) {
  const isAdmin = user.role === 'admin'
  const [plans, setPlans] = useState(null)
  const [plan, setPlan] = useState(null)
  const [edits, setEdits] = useState({})
  const [horizon, setHorizon] = useState(7)
  const [level, setLevel] = useState('expected')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)

  const loadPlans = useCallback(async (selectId) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.get('/allocation/plans')
      setPlans(data)
      const pick = data.find((p) => p.id === selectId) || data[0] || null
      setPlan(pick)
      setEdits({})
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => {
    loadPlans()
  }, [loadPlans])

  const run = async () => {
    setBusy('run')
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/allocation/run', { horizon_days: horizon, planning_level: level })
      await loadPlans(data.id)
      setNotice(`Plan #${data.id} generated in ${data.summary.solve_seconds}s (${data.summary.solver_status.toLowerCase()} solution).`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const accept = async () => {
    setBusy('accept')
    setError('')
    setNotice('')
    try {
      const actions = Object.entries(edits).map(([id, quantity]) => ({ id: Number(id), quantity: Number(quantity) }))
      const { data } = await api.post(`/allocation/plans/${plan.id}/accept`, { actions })
      await loadPlans(data.id)
      setNotice(`Plan #${data.id} accepted${data.modified ? ' with your changes' : ''}. Bed capacity, rosters and equipment stock are updated.`)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy('')
    }
  }

  const grouped = useMemo(() => {
    if (!plan) return []
    return GROUPS.map(([type, label]) => [label, plan.actions.filter((a) => a.type === type)]).filter(([, xs]) => xs.length)
  }, [plan])
  const editable = isAdmin && plan?.status === 'proposed'
  const changed = Object.entries(edits).filter(([id, q]) => plan?.actions.find((a) => a.id === Number(id))?.quantity !== Number(q)).length

  return (
    <div>
      <PageHeader title="Allocation recommendations" subtitle="Optimised beds, nurse shifts and equipment for the forecast peak, with the trade-off explained" />
      <ErrorBox message={error} />
      {notice && (
        <div className="flex items-center gap-2 rounded-lg bg-teal-50 text-teal-900 text-sm p-3 mb-4">
          <CheckCircle2 size={16} /> {notice}
        </div>
      )}

      <div className="card p-4 mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="label">Planning horizon</label>
          <select className="input" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} disabled={!isAdmin}>
            <option value={3}>Next 3 days</option>
            <option value={7}>Next 7 days</option>
            <option value={14}>Next 14 days</option>
          </select>
        </div>
        <div>
          <label className="label">Plan for</label>
          <select className="input" value={level} onChange={(e) => setLevel(e.target.value)} disabled={!isAdmin}>
            <option value="expected">Expected peak</option>
            <option value="p90">90% upper band (cautious)</option>
          </select>
        </div>
        <button className="btn-primary" onClick={run} disabled={!isAdmin || !!busy}>
          {busy === 'run' ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />} Run optimiser
        </button>
        {!isAdmin && <span className="text-xs text-slate-500">Only administrators can generate and accept plans.</span>}
        {plans?.length > 0 && (
          <div className="ml-auto">
            <label className="label">Plan history</label>
            <select className="input" value={plan?.id || ''} onChange={(e) => { setPlan(plans.find((p) => p.id === Number(e.target.value))); setEdits({}) }}>
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} - {p.status} - {p.created_at.slice(0, 16).replace('T', ' ')}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading && !plans ? (
        <Loading />
      ) : busy === 'run' ? (
        <Loading label="Forecasting the peak and solving the allocation..." />
      ) : !plan ? (
        <div className="card p-8 text-center text-sm text-slate-500">No plans yet. {isAdmin ? 'Run the optimiser to generate one.' : 'An administrator can generate one.'}</div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <h2 className="text-lg font-semibold text-slate-900">Plan #{plan.id}</h2>
            <Badge tone={plan.status === 'accepted' ? 'teal' : 'amber'}>{plan.status}</Badge>
            {plan.modified && <Badge tone="blue">modified</Badge>}
            <span className="text-xs text-slate-500">
              {plan.horizon_days}-day horizon, {plan.planning_level === 'p90' ? '90% upper band' : 'expected peak'} - by {plan.created_by}
              {plan.accepted_by && `, accepted by ${plan.accepted_by}`}
            </span>
          </div>
          <div className="grid sm:grid-cols-3 gap-4 mb-4">
            <Compare label="Patients without a bed" before={plan.summary.before.bed_shortfall} after={plan.summary.after.bed_shortfall} />
            <Compare label="Nurse shifts short" before={plan.summary.before.nurse_shift_gap} after={plan.summary.after.nurse_shift_gap} />
            <Compare label="Equipment units short" before={plan.summary.before.equipment_gap} after={plan.summary.after.equipment_gap} />
          </div>
          <div className="card p-4 mb-6">
            <h3 className="font-semibold text-slate-900 mb-1">Trade-off</h3>
            <p className="text-sm text-slate-700">{plan.summary.text}</p>
            <p className="text-xs text-slate-500 mt-2">
              Cost order used by the optimiser: a patient without a bed &gt; a nurse shift short &gt; an equipment unit short &gt; diverting an admission &gt; an
              extra nurse shift &gt; moving equipment &gt; converting a bed &gt; floating a nurse. Recommendations support, and do not replace, the judgement of the
              bed manager.
            </p>
          </div>

          {grouped.map(([label, actions]) => (
            <div key={label} className="card overflow-x-auto mb-4">
              <h3 className="font-semibold text-slate-900 px-4 pt-4 pb-2">
                {label} <span className="text-slate-400 font-normal">({actions.reduce((s, a) => s + a.quantity, 0)})</span>
              </h3>
              <table className="w-full min-w-[640px]">
                <thead>
                  <tr>
                    <th className="th w-72">Action</th>
                    <th className="th w-28">Quantity</th>
                    <th className="th">Why</th>
                  </tr>
                </thead>
                <tbody>
                  {actions.map((a) => (
                    <tr key={a.id}>
                      <td className="td">{describe(a)}</td>
                      <td className="td">
                        {editable ? (
                          <input
                            type="number"
                            min={0}
                            className="input w-20 py-1"
                            value={edits[a.id] ?? a.quantity}
                            onChange={(e) => setEdits({ ...edits, [a.id]: e.target.value === '' ? 0 : Math.max(0, Number(e.target.value)) })}
                          />
                        ) : (
                          <span>
                            {a.quantity}
                            {a.original_quantity != null && <span className="text-xs text-slate-400 ml-1">(was {a.original_quantity})</span>}
                          </span>
                        )}
                      </td>
                      <td className="td text-xs text-slate-600">{a.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
          {plan.actions.length === 0 && <div className="card p-6 text-sm text-slate-500">No changes needed - the current allocation covers the forecast peak.</div>}

          {editable && (
            <div className="sticky bottom-4 card p-4 flex flex-wrap items-center gap-3 shadow-lg">
              <span className="text-sm text-slate-600">
                {changed ? `${changed} action(s) modified. Set a quantity to 0 to drop an action.` : 'Edit any quantity (0 drops an action), then accept.'}
              </span>
              <div className="ml-auto flex gap-2">
                {changed > 0 && (
                  <button className="btn-secondary" onClick={() => setEdits({})} disabled={!!busy}>
                    <RotateCcw size={16} /> Reset edits
                  </button>
                )}
                <button className="btn-primary" onClick={accept} disabled={!!busy}>
                  {busy === 'accept' ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                  {changed ? 'Accept modified plan' : 'Accept plan'}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

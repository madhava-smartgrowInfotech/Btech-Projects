import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowRight, CheckCircle2, Play, RotateCcw, Workflow } from 'lucide-react'
import api, { errorMessage } from '../api'
import { useAuth } from '../lib/auth'
import { TONE_COLOR } from '../lib/hospi'
import { useToast } from '../components/ui/Toast'
import { PageHeader } from '../components/ui/Layout'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Form'
import { Badge, Card, StatCard } from '../components/ui/Display'
import { Alert, EmptyState, ErrorState, SkeletonBlock } from '../components/ui/Feedback'
import { Modal } from '../components/ui/Feedback'
import { Table } from '../components/ui/Table'

const GROUPS = [
  ['bed_conversion', 'Bed conversions'],
  ['diversion', 'Admission diversions'],
  ['nurse_float', 'Nurse floats'],
  ['extra_shift', 'Extra nurse shifts'],
  ['equipment_transfer', 'Equipment transfers'],
]

const HORIZON_OPTS = [
  { value: 3, label: 'Next 3 days' },
  { value: 7, label: 'Next 7 days' },
  { value: 14, label: 'Next 14 days' },
]
const LEVEL_OPTS = [
  { value: 'expected', label: 'Expected peak' },
  { value: 'p90', label: '90% upper band (cautious)' },
]

function describe(a) {
  switch (a.type) {
    case 'bed_conversion':
      return (
        <>
          Facility {a.facility}: {a.from_ward} <ArrowRight size={12} aria-hidden="true" className="inline" /> {a.to_ward} beds
        </>
      )
    case 'diversion':
      return (
        <>
          {a.ward} admissions: Facility {a.facility} <ArrowRight size={12} aria-hidden="true" /> Facility {a.to_facility}
        </>
      )
    case 'nurse_float':
      return (
        <>
          Facility {a.facility} {a.shift}: {a.from_ward} <ArrowRight size={12} aria-hidden="true" /> {a.to_ward} nurses
        </>
      )
    case 'extra_shift':
      return (
        <>
          Facility {a.facility} {a.ward}: extra {a.shift} nurses
        </>
      )
    case 'equipment_transfer':
      return (
        <>
          {a.item}: Facility {a.facility} <ArrowRight size={12} aria-hidden="true" /> Facility {a.to_facility}
        </>
      )
    default:
      return a.type
  }
}

function Compare({ label, before, after }) {
  const delta = after === before ? 'No change' : after < before ? `${after - before}` : `+${after - before}`
  const tone = after < before ? TONE_COLOR.ok : after > before ? TONE_COLOR.critical : undefined
  return <StatCard label={label} value={after} hint={`Current allocation: ${before}`} delta={delta} deltaTone={tone} />
}

export default function Allocation() {
  const { user } = useAuth()
  const toast = useToast()
  const isAdmin = user.role === 'admin'
  const [plans, setPlans] = useState(null)
  const [plansError, setPlansError] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [edits, setEdits] = useState({})
  const [horizon, setHorizon] = useState(7)
  const [level, setLevel] = useState('expected')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  const loadPlans = useCallback(async (selectId) => {
    setLoading(true)
    setPlansError('')
    try {
      const { data } = await api.get('/allocation/plans')
      setPlans(data)
      setSelectedId(selectId ?? data[0]?.id ?? null)
      setEdits({})
    } catch (err) {
      setPlansError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadPlans()
  }, [loadPlans])

  const plan = useMemo(() => plans?.find((p) => p.id === selectedId) ?? plans?.[0] ?? null, [plans, selectedId])
  const editable = isAdmin && plan?.status === 'proposed'
  const changed = plan ? Object.entries(edits).filter(([id, q]) => plan.actions.find((a) => a.id === Number(id))?.quantity !== Number(q)).length : 0

  const run = async () => {
    setBusy('run')
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/allocation/run', { horizon_days: horizon, planning_level: level })
      setPlans((ps) => [data, ...(ps || [])])
      setSelectedId(data.id)
      setEdits({})
      const msg = `Plan #${data.id} generated in ${data.summary.solve_seconds}s (${String(data.summary.solver_status).toLowerCase()} solution).`
      setNotice(msg)
      toast.success(msg)
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
      setPlans((ps) => ps.map((p) => (p.id === data.id ? data : p)))
      setEdits({})
      setConfirmOpen(false)
      const msg = `Plan #${data.id} accepted${data.modified ? ' with your changes' : ''}. Bed capacity, rosters and equipment stock are updated.`
      setNotice(msg)
      toast.success(msg)
    } catch (err) {
      setError(errorMessage(err))
      setConfirmOpen(false)
    } finally {
      setBusy('')
    }
  }

  const grouped = useMemo(() => {
    if (!plan) return []
    return GROUPS.map(([type, label]) => [label, plan.actions.filter((a) => a.type === type)]).filter(([, xs]) => xs.length)
  }, [plan])

  const quantityOf = (a) => (edits[a.id] !== undefined ? edits[a.id] : a.quantity)

  return (
    <>
      <PageHeader
        eyebrow="Allocation"
        title="Allocation recommendations"
        description="Optimised beds, nurse shifts and equipment for the forecast peak, with the trade-off explained."
      />

      {error && (
        <div style={{ marginBottom: 20 }}>
          <Alert tone="error">{error}</Alert>
        </div>
      )}
      {notice && (
        <div style={{ marginBottom: 20 }}>
          <Alert tone="success">
            <CheckCircle2 size={16} aria-hidden="true" style={{ verticalAlign: '-3px', marginRight: 6 }} />
            {notice}
          </Alert>
        </div>
      )}
      {!isAdmin && (
        <div style={{ marginBottom: 20 }}>
          <Alert tone="info">Only administrators can generate and accept plans. You can review every plan here.</Alert>
        </div>
      )}

      <Card className="allocation-controls" style={{ marginBottom: 28 }}>
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <Select label="Planning horizon" options={HORIZON_OPTS} value={horizon} onChange={(e) => setHorizon(Number(e.target.value))} disabled={!isAdmin || !!busy} />
          <Select label="Plan for" options={LEVEL_OPTS} value={level} onChange={(e) => setLevel(e.target.value)} disabled={!isAdmin || !!busy} />
          <Button variant="primary" icon={Play} onClick={run} loading={busy === 'run'} disabled={!isAdmin || (!!busy && busy !== 'run')}>
            Run optimiser
          </Button>
          {plans?.length > 0 && (
            <div style={{ marginLeft: 'auto' }}>
              <Select
                label="Plan history"
                value={plan?.id ?? ''}
                onChange={(e) => {
                  setSelectedId(Number(e.target.value))
                  setEdits({})
                }}
                options={plans.map((p) => ({
                  value: p.id,
                  label: `#${p.id} · ${p.status} · ${p.created_at.slice(0, 16).replace('T', ' ')}`,
                }))}
              />
            </div>
          )}
        </div>
      </Card>

      {loading && !plans && <SkeletonBlock rows={6} label="Loading plans" />}
      {plansError && !plans && <ErrorState title="Plans could not load" error={plansError} onRetry={() => loadPlans()} />}
      {busy === 'run' && <SkeletonBlock rows={6} label="Forecasting the peak and solving the allocation" />}

      {plans && !plan && busy !== 'run' && (
        <EmptyState icon={Workflow} title="No plans yet" action={isAdmin ? <Button variant="primary" icon={Play} onClick={run}>Run optimiser</Button> : undefined}>
          {isAdmin ? 'Run the optimiser to generate the first plan for the forecast peak.' : 'An administrator can generate a plan from the forecast.'}
        </EmptyState>
      )}

      {plan && busy !== 'run' && (
        <>
          <div className="row" style={{ marginBottom: 14 }}>
            <h2 className="display-sm">Plan #{plan.id}</h2>
            <Badge tone={plan.status === 'accepted' ? 'pass' : 'closed'}>{plan.status}</Badge>
            {plan.modified && <Badge tone="info">modified</Badge>}
            <span className="small muted">
              {plan.horizon_days}-day horizon, {plan.planning_level === 'p90' ? '90% upper band' : 'expected peak'}, by {plan.created_by}
              {plan.accepted_by && `, accepted by ${plan.accepted_by}`}
            </span>
          </div>

          <div className="grid grid-3" style={{ '--gap': '16px', marginBottom: 20 }}>
            <Compare label="Patients without a bed" before={plan.summary.before.bed_shortfall} after={plan.summary.after.bed_shortfall} />
            <Compare label="Nurse shifts short" before={plan.summary.before.nurse_shift_gap} after={plan.summary.after.nurse_shift_gap} />
            <Compare label="Equipment units short" before={plan.summary.before.equipment_gap} after={plan.summary.after.equipment_gap} />
          </div>

          <Card title="Trade-off" style={{ marginBottom: 24 }}>
            <p>{plan.summary.text}</p>
            <p className="tiny muted" style={{ marginTop: 12 }}>
              Cost order used by the optimiser: a patient without a bed is worse than a nurse shift short, which is worse than an equipment unit short,
              then diverting an admission, an extra nurse shift, moving equipment, converting a bed and floating a nurse. Recommendations support, and do
              not replace, the judgement of the bed manager.
            </p>
          </Card>

          {grouped.length === 0 && (
            <Card>
              <p>No changes needed. The current allocation covers the forecast peak.</p>
            </Card>
          )}

          <div className="stack" style={{ '--gap': '20px' }}>
            {grouped.map(([label, actions]) => (
              <Card key={label} title={`${label} (${actions.reduce((s, a) => s + a.quantity, 0)})`} className="table-scroll-x">
                <Table
                  caption={label}
                  rows={actions}
                  rowKey={(a) => a.id}
                  pageSize={10}
                  columns={[
                    { key: 'action', label: 'Action', sortable: false, render: (a) => describe(a) },
                    {
                      key: 'quantity',
                      label: 'Quantity',
                      sortable: false,
                      numeric: true,
                      render: (a) =>
                        editable ? (
                          <input
                            type="number"
                            min={0}
                            className="input"
                            style={{ width: 96, padding: '6px 8px' }}
                            aria-label={`Quantity for ${a.type.replace('_', ' ')} ${a.id}`}
                            value={quantityOf(a)}
                            onChange={(e) => setEdits((x) => ({ ...x, [a.id]: e.target.value === '' ? 0 : Math.max(0, Number(e.target.value)) }))}
                          />
                        ) : (
                          <span>
                            {a.quantity}
                            {a.original_quantity != null && <span className="tiny muted"> (was {a.original_quantity})</span>}
                          </span>
                        ),
                    },
                    { key: 'reason', label: 'Why', sortable: false, render: (a) => <span className="small">{a.reason}</span> },
                  ]}
                />
              </Card>
            ))}
          </div>

          {editable && (
            <Card flat className="plan-actions" style={{ marginTop: 24 }}>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <span className="small">
                  {changed ? `${changed} action(s) changed. A quantity of 0 drops the action.` : 'Edit any quantity (0 drops an action), then accept the plan.'}
                </span>
                <div className="row">
                  {changed > 0 && (
                    <Button icon={RotateCcw} onClick={() => setEdits({})} disabled={!!busy}>
                      Reset edits
                    </Button>
                  )}
                  <Button variant="primary" icon={CheckCircle2} onClick={() => setConfirmOpen(true)} disabled={!!busy}>
                    {changed ? 'Accept modified plan' : 'Accept plan'}
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </>
      )}

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title={`Accept plan #${plan?.id ?? ''}?`}
        describedBy="accept-copy"
        footer={
          <>
            <Button onClick={() => setConfirmOpen(false)} disabled={busy === 'accept'}>
              Cancel
            </Button>
            <Button variant="primary" icon={CheckCircle2} onClick={accept} loading={busy === 'accept'}>
              Accept
            </Button>
          </>
        }
      >
        <p id="accept-copy">
          This updates bed capacity, nurse rosters and equipment stock to the plan{changed ? ', with your changes' : ''}. It cannot be undone from this
          screen.
        </p>
      </Modal>
    </>
  )
}

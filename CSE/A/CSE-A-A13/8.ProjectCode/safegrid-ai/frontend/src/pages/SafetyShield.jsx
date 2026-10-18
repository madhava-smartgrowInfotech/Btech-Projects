import { useMemo, useState } from 'react'
import { CheckCircle2, Hash, ListChecks, Percent, ShieldAlert, ShieldCheck, ShieldX, Sigma } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { api } from '../services/api'
import { useAsync } from '../lib/useAsync'
import { ACTION_LABEL, CONSTRAINT_LABEL, kw, num, pct, timeOf, titleize } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Badge, Card, CardHeader, KeyValueList, StatCard, Table } from '../components/ui/display'
import { Button, Input, Select } from '../components/ui/controls'
import { EmptyState, ErrorState, Modal, Skeleton, useToast } from '../components/ui/feedback'
import { Tabs } from '../components/ui/navigation'
import { SlideUp, Stagger } from '../components/motion'
import ActionLane, { Checks } from '../components/safegrid/ActionLane'
import { ShieldBadge } from '../components/safegrid/badges'

const TYPES = Object.entries(ACTION_LABEL).map(([value, label]) => ({ value, label }))

function DryRun({ agents }) {
  const toast = useToast()
  const [form, setForm] = useState({ agent_id: '', action_type: 'export_power', power_kw: '1000', duration_minutes: '15' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const agentId = form.agent_id || agents[0]?.agent_id || ''
  const power = Number(form.power_kw)
  const duration = Number(form.duration_minutes)
  const invalid = !agentId || !Number.isFinite(power) || power < 0 || !Number.isFinite(duration) || duration < 1

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const action = { agent_id: agentId, action_type: form.action_type, power_kw: power, duration_minutes: duration, target_node: null, reason_codes: ['OPERATOR_TEST'], confidence: 1 }
      const r = await api.dryRun(agentId, action)
      setResult(r)
      toast({ tone: 'success', title: `Shield decision: ${r.shield?.status}`, message: 'Dry run only - nothing was applied to the grid.' })
    } catch (err) {
      setResult(null)
      setError(err.message)
    }
    setBusy(false)
  }

  return (
    <Card>
      <CardHeader title="Try an action against the shield" subtitle="Craft any proposal, including absurd ones. It is validated against the current grid state and never applied." />
      <form className="card-body stack" onSubmit={submit}>
        <div className="form-grid">
          <Select label="Agent" value={agentId} onChange={set('agent_id')} options={agents.length ? agents.map((a) => ({ value: a.agent_id, label: a.agent_id })) : [{ value: '', label: 'No agents' }]} />
          <Select label="Action" value={form.action_type} onChange={set('action_type')} options={TYPES} />
          <Input label="Power (kW)" type="number" min="0" step="0.1" value={form.power_kw} onChange={set('power_kw')} error={Number.isFinite(power) && power >= 0 ? undefined : 'Enter a power of 0 or more'} />
          <Input label="Duration (min)" type="number" min="1" value={form.duration_minutes} onChange={set('duration_minutes')} error={Number.isFinite(duration) && duration >= 1 ? undefined : 'At least 1 minute'} />
        </div>
        <div className="row">
          <Button type="submit" variant="primary" icon={ShieldCheck} loading={busy} disabled={invalid}>
            Validate
          </Button>
          {result && <Button variant="ghost" onClick={() => setResult(null)}>Clear result</Button>}
        </div>
        {error && <ErrorState title="The shield could not evaluate that action" error={new Error(error)} />}
        {result && <ActionLane record={result} />}
      </form>
    </Card>
  )
}

function flattenLimits(obj) {
  return Object.entries(obj || {}).filter(([, v]) => typeof v !== 'object')
}

function Constraints() {
  const { data, loading, error, reload } = useAsync(() => api.constraints(), [])
  const nodes = data ? Object.entries(data.node_limits || {}) : []
  return (
    <Card>
      <CardHeader title="Active constraints" subtitle="The limits the shield enforces for the current run" />
      <div className="card-body">
        {loading ? <Skeleton height={160} radius={12} /> : error ? <ErrorState title="Constraints unavailable" error={error} onRetry={reload} /> : (
          <div className="stack">
            <KeyValueList
              items={flattenLimits(data).map(([k, v]) => {
                const [label, unit] = CONSTRAINT_LABEL[k] || [titleize(k), '']
                return [label, `${num(v, v % 1 ? 3 : 0)}${unit ? ` ${unit}` : ''}`]
              })}
            />
            {nodes.length > 0 && (
              <div className="table-wrap">
                <table className="table">
                  <caption className="sr-only">Per-node limits</caption>
                  <thead>
                    <tr><th scope="col">Node</th><th scope="col" className="num">Import</th><th scope="col" className="num">Export</th><th scope="col" className="num">Battery</th><th scope="col" className="num">SOC band</th></tr>
                  </thead>
                  <tbody>
                    {nodes.map(([id, l]) => (
                      <tr key={id}>
                        <td><strong>{id}</strong></td>
                        <td className="num">{kw(l.max_import_kw, 0)}</td>
                        <td className="num">{kw(l.max_export_kw, 0)}</td>
                        <td className="num">{l.storage_capacity_kwh ? `${num(l.storage_capacity_kwh, 0)} kWh` : '-'}</td>
                        <td className="num">{l.storage_capacity_kwh ? `${num(l.soc_min * 100, 0)}-${num(l.soc_max * 100, 0)}%` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

function EventDetail({ e, onClose }) {
  return (
    <Modal open={!!e} onClose={onClose} title={e ? `Safety event #${e.event_id}` : ''} footer={<Button onClick={onClose}>Close</Button>}>
      {e && (
        <div className="stack">
          <KeyValueList
            items={[
              ['Outcome', <ShieldBadge key="s" status={e.status} />],
              ['Agent', `${e.agent_id} (${e.node_id})`],
              ['Simulation time', `${e.sim_time} (step ${e.step})`],
              ['Requested', `${ACTION_LABEL[e.requested_action?.action_type] || e.requested_action?.action_type} ${kw(e.requested_action?.power_kw)}`],
              ['Executed', e.validated_action ? `${ACTION_LABEL[e.validated_action.action_type] || e.validated_action.action_type} ${kw(e.validated_action.power_kw)}` : 'Nothing executed'],
              ['Decision source', titleize(e.decision_source)],
            ]}
          />
          <div>
            <div className="faint" style={{ marginBottom: 8 }}>Checks</div>
            <Checks checks={e.checks} />
          </div>
          {(e.violations || []).length > 0 && (
            <div className="viol-list">
              {e.violations.map((v, i) => (
                <div className="viol" key={i}><strong className="mono">{v.code}</strong> {v.message}</div>
              ))}
            </div>
          )}
          <p className="faint mono break">
            {timeOf(e.timestamp)} · hash {e.hash?.slice(0, 20)}… · prev {e.prev_hash?.slice(0, 20)}…
          </p>
        </div>
      )}
    </Modal>
  )
}

export default function SafetyShield() {
  const { safety, summary, agents, ready, error, refresh, step, busy, status } = useSimulation()
  const [filter, setFilter] = useState('all')
  const [open, setOpen] = useState(null)
  const events = useMemo(() => (safety.events || []).filter((e) => filter === 'all' || e.status === filter), [safety, filter])
  const finished = !!status && status.step >= status.total_steps
  const caused = summary?.violations_caused_by_actions ?? 0
  const columns = [
    { key: 'sim_time', label: 'Time' },
    { key: 'agent_id', label: 'Agent' },
    { key: 'status', label: 'Outcome', render: (e) => <ShieldBadge status={e.status} /> },
    { key: 'violations', label: 'Violations', hideSm: true, sortable: false, render: (e) => (e.violations || []).map((v) => v.code).join(', ') || <span className="faint">{e.event_type === 'AGENT_ANOMALY' ? titleize(e.decision_source) : '-'}</span> },
    { key: 'req', label: 'Requested', num: true, render: (e) => kw(e.requested_action?.power_kw), sortValue: (e) => e.requested_action?.power_kw },
    { key: 'exec', label: 'Executed', num: true, render: (e) => kw(e.validated_action?.power_kw ?? 0), sortValue: (e) => e.validated_action?.power_kw ?? 0 },
  ]
  return (
    <div className="stack">
      <PageHeader
        title="Safety shield"
        description="Deterministic checks between every AI proposal and the grid. Each decision is written to a hash-chained log, so later edits are detectable."
        actions={safety.chain_valid === null ? null : <Badge tone={safety.chain_valid ? 'safe' : 'danger'} dot>Audit chain {safety.chain_valid ? 'valid' : 'broken'}</Badge>}
      />

      <Stagger className="stat-grid">
        <StatCard loading={!ready} icon={ListChecks} label="Proposals checked" value={summary?.proposals ?? 0} />
        <StatCard loading={!ready} icon={CheckCircle2} label="Approved" value={summary?.approved ?? 0} />
        <StatCard loading={!ready} icon={ShieldAlert} tone="warn" label="Projected (scaled down)" value={summary?.projected ?? 0} />
        <StatCard loading={!ready} icon={ShieldX} tone={summary?.rejected ? 'danger' : undefined} label="Rejected" value={summary?.rejected ?? 0} />
        <StatCard loading={!ready} icon={Sigma} tone="info" label="Violations raw proposals would cause" value={summary?.violations_without_shield ?? 0} />
        <StatCard loading={!ready} icon={ShieldCheck} tone={caused ? 'danger' : undefined} label="Violations caused by executed actions" value={caused} />
        <StatCard loading={!ready} icon={Hash} label="Audit log entries" value={safety.total || 0} />
        <StatCard loading={!ready} icon={Percent} tone="warn" label="Intervention rate" value={summary?.intervention_rate == null ? '-' : pct(summary.intervention_rate, 1)} delta="projected + rejected" />
      </Stagger>

      <SlideUp>
          <Card>
            <CardHeader
              title="Safety events"
              subtitle="Click a row for the full check breakdown and hashes"
              actions={<Tabs label="Filter by outcome" value={filter} onChange={setFilter} tabs={[{ value: 'all', label: 'All' }, { value: 'projected', label: 'Projected' }, { value: 'rejected', label: 'Rejected' }]} />}
            />
            {error && !safety.events.length ? (
              <ErrorState title="Safety log unavailable" error={new Error(error)} onRetry={refresh} />
            ) : (
              <Table
                caption="Safety events"
                columns={columns}
                rows={events}
                rowKey={(e) => e.event_id}
                pageSize={8}
                loading={!ready}
                onRowClick={setOpen}
                empty={
                  <EmptyState icon={ShieldCheck} title={filter === 'all' ? 'No safety events yet' : `No ${filter} events`} actions={filter === 'all' ? <Button variant="primary" disabled={!!busy || finished} onClick={step}>Run one step</Button> : <Button onClick={() => setFilter('all')}>Show all</Button>}>
                    {filter === 'all' ? 'The shield logs every intervention and every fallback decision. Run the simulation, or pick the unsafe AI action scenario to see it intervene.' : 'Nothing has been decided that way in this run.'}
                  </EmptyState>
                }
              />
            )}
          </Card>
      </SlideUp>
      <div className="grid grid-2 top-aligned">
        <SlideUp inView><DryRun agents={agents} /></SlideUp>
        <SlideUp inView delay={0.06}><Constraints /></SlideUp>
      </div>
      <EventDetail e={open} onClose={() => setOpen(null)} />
    </div>
  )
}

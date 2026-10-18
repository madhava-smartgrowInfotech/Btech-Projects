import { useState } from 'react'
import { Bot } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { api } from '../services/api'
import { useAsync } from '../lib/useAsync'
import { ACTION_LABEL, ROLE_LABEL, kw, num, pct, titleize } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Badge, Card, CardHeader, KeyValueList, Table } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import { SlideUp, Stagger } from '../components/motion'
import ActionLane from '../components/safegrid/ActionLane'
import { ShieldBadge, SourceBadge } from '../components/safegrid/badges'

function AgentCard({ a, selected, onPick }) {
  const l = a.latest
  return (
    <button type="button" className={`agent-card${selected ? ' selected' : ''}`} aria-pressed={selected} onClick={() => onPick(a.agent_id)}>
      <div className="agent-card-head">
        <strong>{a.agent_id}</strong>
        <Badge>{ROLE_LABEL[a.role] || titleize(a.role)}</Badge>
      </div>
      <KeyValueList
        items={[
          ['Node', a.node_id],
          ['Battery SOC', a.soc == null ? '-' : pct(a.soc)],
          ['Local voltage', `${num(a.voltage_pu, 3)} pu`],
          ['Grid exchange', kw(a.exchange_kw)],
          ['Latest proposal', l ? `${ACTION_LABEL[l.proposal.action_type] || l.proposal.action_type} ${kw(l.proposal.power_kw)}` : '-'],
          ['Shield result', l ? <ShieldBadge status={l.shield.status} /> : '-'],
          ['Decision source', l ? <SourceBadge source={l.decision_source} /> : '-'],
        ]}
      />
    </button>
  )
}

export default function AgentMonitor() {
  const { agents, status, ready, error, refresh, step, busy } = useSimulation()
  const [selected, setSelected] = useState(null)
  const id = selected || agents[0]?.agent_id
  const detail = useAsync(() => api.agent(id), [id, status?.step, status?.run_id], { enabled: !!id })
  const d = detail.data
  const latest = d?.latest
  const finished = !!status && status.step >= status.total_steps

  const columns = [
    { key: 'time', label: 'Time' },
    { key: 'proposal', label: 'Proposal', render: (h) => ACTION_LABEL[h.proposal.action_type] || h.proposal.action_type, sortValue: (h) => h.proposal.action_type },
    { key: 'kw', label: 'Requested', num: true, render: (h) => kw(h.proposal.power_kw), sortValue: (h) => h.proposal.power_kw },
    { key: 'shield', label: 'Shield', render: (h) => <ShieldBadge status={h.shield.status} />, sortValue: (h) => h.shield.status },
    { key: 'exec', label: 'Executed', num: true, render: (h) => kw(h.executed_power_kw), sortValue: (h) => h.executed_power_kw },
    { key: 'source', label: 'Source', hideSm: true, render: (h) => <SourceBadge source={h.decision_source} />, sortValue: (h) => h.decision_source },
    { key: 'lat', label: 'Latency', num: true, hideSm: true, render: (h) => `${num(h.latency_ms, 1)} ms`, sortValue: (h) => h.latency_ms },
  ]

  return (
    <div className="stack">
      <PageHeader title="Agent monitor" description="Each agent perceives its node, proposes one action per step and never touches the grid directly. If the LLM fails, a labelled fallback policy decides instead." />

      {!ready ? (
        <div className="grid grid-3">
          {[0, 1, 2].map((i) => <Skeleton key={i} height={300} radius={12} />)}
        </div>
      ) : error && !agents.length ? (
        <ErrorState title="Agents unavailable" error={new Error(error)} onRetry={refresh} />
      ) : (
        <Stagger className="grid grid-3">
          {agents.map((a) => <AgentCard key={a.agent_id} a={a} selected={id === a.agent_id} onPick={setSelected} />)}
        </Stagger>
      )}

      {ready && agents.length > 0 && (
        detail.loading && !d ? (
          <Skeleton height={220} radius={12} />
        ) : detail.error ? (
          <ErrorState title={`Could not load ${id}`} error={detail.error} onRetry={detail.reload} />
        ) : !latest ? (
          <Card>
            <EmptyState icon={Bot} title={`No decisions yet for ${id}`} actions={<button type="button" className="btn btn-primary" disabled={!!busy || finished} onClick={step}>Run one step</button>}>
              The agent proposes an action at every simulation step. Run a step to see its proposal, the shield decision and the context it saw.
            </EmptyState>
          </Card>
        ) : (
          <>
            <SlideUp>
              <Card>
                <CardHeader title={`${id}: latest decision`} subtitle={`Simulation time ${latest.time}`} />
                <div className="card-body"><ActionLane record={latest} /></div>
              </Card>
            </SlideUp>
            <div className="split">
              <SlideUp inView>
                <Card>
                  <CardHeader title="Recent decisions" subtitle="Newest first - click a header to sort" />
                  <Table caption={`Recent decisions of ${id}`} columns={columns} rows={[...d.history].reverse()} rowKey={(h) => h.step} pageSize={8} />
                </Card>
              </SlideUp>
              <SlideUp inView delay={0.08}>
                <Card>
                  <CardHeader title="Context the agent saw" subtitle="Structured inputs for the latest decision" />
                  <div className="card-body">
                    <KeyValueList items={Object.entries(latest.explanation?.context_used || {}).map(([k, v]) => [titleize(k), typeof v === 'number' ? num(v, 3) : String(v)])} />
                  </div>
                </Card>
              </SlideUp>
            </div>
          </>
        )
      )}
    </div>
  )
}

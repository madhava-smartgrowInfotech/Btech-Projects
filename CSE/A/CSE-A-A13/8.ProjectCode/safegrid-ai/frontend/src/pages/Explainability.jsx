import { useMemo, useState } from 'react'
import { FileSearch } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { kw, num, titleize } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Badge, Card, CardHeader, KeyValueList } from '../components/ui/display'
import { Button } from '../components/ui/controls'
import { EmptyState, Skeleton } from '../components/ui/feedback'
import { Tabs } from '../components/ui/navigation'
import { SlideUp } from '../components/motion'
import ActionLane from '../components/safegrid/ActionLane'
import { ShieldBadge, SourceBadge } from '../components/safegrid/badges'

/** Only structured facts are shown: inputs, decision factors, action, safety checks, outcome. No model reasoning text. */
export default function Explainability() {
  const { agents, ready, step, busy, status } = useSimulation()
  const records = useMemo(() => agents.map((a) => a.latest).filter(Boolean), [agents])
  const [pick, setPick] = useState(null)
  const rec = records.find((r) => r.agent_id === pick) || records[0]
  const finished = !!status && status.step >= status.total_steps

  const header = <PageHeader title="Explainability" description="Why each agent did what it did and what the shield changed: the inputs, the decision factors and the safety outcome. No model chain-of-thought is requested or stored." />
  if (!ready) return <div className="stack">{header}<Skeleton height={320} radius={12} /></div>
  if (!rec) {
    return (
      <div className="stack">
        {header}
        <Card>
          <EmptyState icon={FileSearch} title="No decisions to explain yet" actions={<Button variant="primary" disabled={!!busy || finished} loading={busy === 'advance one step'} onClick={step}>Run one step</Button>}>
            Explanations are generated for every agent decision. Run a step and the reasoning inputs and safety result will appear here.
          </EmptyState>
        </Card>
      </div>
    )
  }
  const ex = rec.explanation
  return (
    <div className="stack">
      {header}
      <Tabs label="Agent" value={rec.agent_id} onChange={setPick} tabs={records.map((r) => ({ value: r.agent_id, label: r.agent_id }))} />
      <SlideUp key={rec.agent_id}>
        <Card>
          <CardHeader title={`${rec.agent_id} at ${rec.time}`} subtitle="Proposal, shield decision and what actually ran" />
          <div className="card-body"><ActionLane record={rec} /></div>
        </Card>
      </SlideUp>
      <div className="grid grid-2">
        <SlideUp inView>
          <Card>
            <CardHeader title="Why the agent proposed this" />
            <div className="card-body stack">
              <p>
                <strong>{ex.decision_label}</strong> {num(ex.power_kw)} kW with confidence {(ex.confidence * 100).toFixed(0)}%.
              </p>
              <ul className="factor-list">{ex.decision_factors.map((f) => <li key={f}>{f}</li>)}</ul>
              <div className="row">{ex.reason_codes.map((code) => <Badge key={code} className="mono">{code}</Badge>)}</div>
              <p className="row">
                Decision source: <SourceBadge source={ex.decision_source} /> <span className="faint">{ex.decision_source_text}</span>
              </p>
              {ex.fallback_reason && <p className="faint mono break">{ex.fallback_reason}</p>}
            </div>
          </Card>
        </SlideUp>
        <SlideUp inView delay={0.06}>
          <Card>
            <CardHeader title="What the agent knew" subtitle="Context supplied at decision time" />
            <div className="card-body"><KeyValueList items={Object.entries(ex.context_used).map(([k, v]) => [titleize(k), typeof v === 'number' ? num(v, 3) : String(v)])} /></div>
          </Card>
        </SlideUp>
        <SlideUp inView>
          <Card>
            <CardHeader title="Safety result" />
            <div className="card-body stack">
              <p className="row">Outcome: <ShieldBadge status={ex.safety_result} /> Executed <strong>{kw(ex.executed_power_kw)}</strong> of {kw(ex.power_kw)} requested.</p>
              {ex.shield_violations.length === 0 ? (
                <p className="faint">All checks passed for the requested action.</p>
              ) : (
                <div className="viol-list">
                  {ex.shield_violations.map((v, i) => (
                    <div className="viol" key={i}><strong className="mono">{v.code}</strong> at {v.component}: requested {num(v.requested)}, allowed {num(v.allowed)}</div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </SlideUp>
        <SlideUp inView delay={0.06}>
          <Card>
            <CardHeader title="Raw record" subtitle="The explanation exactly as the API returns it" />
            <div className="card-body"><pre className="json" tabIndex={0} aria-label="Raw explanation JSON">{JSON.stringify(ex, null, 2)}</pre></div>
          </Card>
        </SlideUp>
      </div>
    </div>
  )
}

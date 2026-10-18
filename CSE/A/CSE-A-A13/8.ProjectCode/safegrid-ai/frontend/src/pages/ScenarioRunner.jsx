import { useEffect, useRef, useState } from 'react'
import { FlaskConical, Play, Timer } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { api } from '../services/api'
import { num, pct, titleize } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Badge, Card, CardHeader, KeyValueList } from '../components/ui/display'
import { Button, Input } from '../components/ui/controls'
import { EmptyState, ErrorState, Modal, Skeleton, useToast } from '../components/ui/feedback'
import { GroupedBarChart, Legend, useChartColors } from '../components/charts'
import { SlideUp, Stagger } from '../components/motion'

const ARM_LABEL = {
  baseline_rule: 'Rule-based controller',
  agents_unshielded: 'AI agents, shield off',
  safegrid_shielded: 'SafeGrid-AI (agents + shield)',
}

function summaryItems(s) {
  return [
    ['Proposals', s.proposals],
    ['Approved', s.approved],
    ['Projected (scaled down)', s.projected],
    ['Rejected', s.rejected],
    ['Violations the raw proposals would cause', s.violations_without_shield],
    ['Violations caused by executed actions', s.violations_caused_by_actions],
    ['Steps with pre-existing grid stress (all idle)', s.violation_steps_no_action],
    ['Voltage violation steps', s.voltage_violation_steps],
    ['Line overload events', s.line_overload_events],
    ['Energy cost (INR, illustrative)', num(s.total_cost, 2)],
    ['Renewable utilisation', pct(s.renewable_utilization, 1)],
    ['Battery throughput', `${num(s.battery_throughput_kwh, 1)} kWh`],
    ['Fallback rate', pct(s.fallback_rate, 1)],
    ['Average decision latency', `${num(s.avg_decision_latency_ms, 1)} ms`],
    ['Audit chain valid', s.safety_chain_valid ? 'Yes' : 'No'],
  ]
}

const METRIC_ROWS = [
  ['violation_steps_caused_by_actions', 'Steps with violations caused by actions', 0],
  ['violations_without_shield', 'Violations raw proposals would cause', 0],
  ['voltage_violation_steps', 'Voltage violation steps', 0],
  ['line_overload_events', 'Line overload events', 0],
  ['total_cost', 'Energy cost (INR)', 1],
  ['renewable_utilization', 'Renewable utilisation', 3],
  ['intervention_rate', 'Shield intervention rate', 3],
  ['fallback_rate', 'Fallback rate', 3],
  ['avg_decision_latency_ms', 'Decision latency (ms)', 2],
]

function Experiment() {
  const toast = useToast()
  const c = useChartColors()
  const [exp, setExp] = useState(null)
  const [job, setJob] = useState(null)
  const [seeds, setSeeds] = useState('0')
  const [steps, setSteps] = useState('8')
  const [elapsed, setElapsed] = useState(0)
  const [err, setErr] = useState(null)
  const [starting, setStarting] = useState(false)
  const jobRef = useRef(null)
  jobRef.current = job

  useEffect(() => {
    if (!job || job.status !== 'running') return undefined
    const t = setInterval(async () => {
      try {
        const r = await api.experiment(job.exp_id)
        if (r.status === 'failed') {
          setJob(r)
          setErr(r.error)
        } else if (r.results || r.overall || r.by_scenario) {
          setExp(r.results || r)
          setJob({ ...jobRef.current, status: 'completed' })
          toast({ tone: 'success', title: 'Comparison finished', message: 'Results are ready below.' })
        }
      } catch {
        /* the job is still running */
      }
    }, 1500)
    return () => clearInterval(t)
  }, [job, toast])

  useEffect(() => {
    if (job?.status !== 'running') return undefined
    const t0 = Date.now()
    setElapsed(0)
    const t = setInterval(() => setElapsed(Math.round((Date.now() - t0) / 1000)), 1000)
    return () => clearInterval(t)
  }, [job?.status, job?.exp_id])

  const seedList = seeds.split(',').map((x) => parseInt(x.trim(), 10)).filter((x) => !Number.isNaN(x))
  const stepsN = Number(steps)
  const seedErr = seedList.length === 0 ? 'Enter at least one seed, e.g. 0,1,2' : seedList.length > 20 ? 'At most 20 seeds' : undefined
  const stepErr = !Number.isInteger(stepsN) || stepsN < 4 || stepsN > 96 ? 'Between 4 and 96 steps' : undefined

  const run = async (e) => {
    e.preventDefault()
    setErr(null)
    setExp(null)
    setStarting(true)
    try {
      setJob(await api.experimentRun({ seeds: seedList, steps: stepsN }))
    } catch (ex) {
      setErr(ex.message)
    }
    setStarting(false)
  }

  const running = job?.status === 'running'
  const arms = exp ? Object.keys(exp.overall) : []
  const armColor = (a, i) => [c.text3, c.warn, c.accent][i % 3]
  const scenarioNames = exp ? Object.keys(exp.by_scenario) : []
  const chartData = exp ? scenarioNames.map((sc) => ({ scenario: titleize(sc), ...Object.fromEntries(arms.map((a) => [a, exp.by_scenario[sc][a]?.violation_steps_caused_by_actions?.mean ?? 0])) })) : []

  return (
    <Card>
      <CardHeader title="Strategy comparison" subtitle="Run every scenario with identical seeds under three control strategies and compare the outcome. Nothing is precomputed - each number comes from a real simulation run." />
      <form className="card-body stack" onSubmit={run}>
        <div className="form-grid">
          <Input label="Seeds" hint="Comma separated, e.g. 0,1,2" value={seeds} onChange={(e) => setSeeds(e.target.value)} error={seedErr} />
          <Input label="Steps per run" type="number" min="4" max="96" value={steps} onChange={(e) => setSteps(e.target.value)} error={stepErr} />
        </div>
        <div className="row">
          <Button type="submit" variant="primary" icon={FlaskConical} loading={running || starting} disabled={!!seedErr || !!stepErr}>
            {running ? 'Running comparison…' : 'Run comparison'}
          </Button>
          {running ? (
            <span className="faint" role="status">Running {7 * 3 * seedList.length} simulations · {elapsed}s elapsed · roughly {Math.max(1, Math.round((7 * 3 * seedList.length * stepsN * 0.2) / 60))} min in total</span>
          ) : (
            <span className="faint">{7 * 3 * (seedList.length || 0)} simulations (7 scenarios × 3 strategies × {seedList.length || 0} seed{seedList.length === 1 ? '' : 's'}). More seeds and steps take longer.</span>
          )}
        </div>
        {err && <ErrorState title="The comparison failed" error={new Error(err)} />}
        {running && <Skeleton height={140} radius={12} />}
        {exp && (
          <div className="stack">
            <div className="table-wrap">
              <table className="table">
                <caption className="sr-only">Mean of each metric across scenarios and seeds, per strategy</caption>
                <thead>
                  <tr>
                    <th scope="col">Metric (mean over scenarios and seeds)</th>
                    {arms.map((a) => <th key={a} scope="col" className="num">{ARM_LABEL[a] || exp.spec.arm_definitions[a]}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {METRIC_ROWS.map(([k, label, d]) => (
                    <tr key={k}>
                      <td>{label}</td>
                      {arms.map((a) => <td key={a} className="num">{exp.overall[a][k] ? num(exp.overall[a][k].mean, d) : '-'}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h3 className="mini-title">Steps with violations caused by actions, per scenario</h3>
              <Legend items={arms.map((a, i) => ({ label: ARM_LABEL[a] || a, color: armColor(a, i) }))} />
              <div style={{ height: 260 }}>
                <GroupedBarChart data={chartData} xKey="scenario" yDomain={[0, 'auto']} valueFormat={(v) => num(v, 1)} series={arms.map((a, i) => ({ key: a, label: ARM_LABEL[a] || a, color: armColor(a, i) }))} />
              </div>
            </div>
            <div className="stack faint" style={{ gap: 6 }}>
              <p>Every figure comes from simulation runs on the demo 3-node low-voltage feeder, not from field data.</p>
              <p>Violations caused by actions counts limit violations that are new or worse than the grid with every agent idle - exactly what the shield exists to prevent. Violations the raw proposals would cause shows what would have happened without it.</p>
              <p>AI agents here use the mock LLM, which is deterministic; a real LLM will behave differently.</p>
            </div>
          </div>
        )}
      </form>
    </Card>
  )
}

export default function ScenarioRunner() {
  const { scenarios, runScenario, status, busy, ready } = useSimulation()
  const [running, setRunning] = useState(null)
  const [results, setResults] = useState({})
  const [open, setOpen] = useState(null)
  const go = async (id) => {
    setRunning(id)
    const r = await runScenario(id, { seed: 42, provider: 'mock', step_delay_s: 0 })
    if (r) setResults((prev) => ({ ...prev, [id]: r }))
    setRunning(null)
  }
  const live = status?.status === 'running'
  const openScenario = scenarios.find((s) => s.id === open)

  return (
    <div className="stack">
      <PageHeader title="Scenarios" description="Seven seeded, reproducible scenarios. Some deliberately inject unsafe or malformed AI proposals so you can watch the shield step in. Running one makes it the current run on every screen." />
      {!ready ? (
        <div className="grid grid-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={170} radius={12} />)}</div>
      ) : !scenarios.length ? (
        <Card><EmptyState icon={FlaskConical} title="No scenarios available">The scenario list could not be loaded from the API. Check that the backend is running.</EmptyState></Card>
      ) : (
        <Stagger className="grid grid-2">
          {scenarios.map((s) => {
            const r = results[s.id]
            const isRunning = running === s.id
            return (
              <Card key={s.id} className="scenario-card">
                <CardHeader title={s.name} subtitle={`${s.n_steps} steps from ${s.start_time}`} actions={<>{s.faults.length > 0 && <Badge tone="warn" dot>{s.faults.length} injected fault{s.faults.length > 1 ? 's' : ''}</Badge>}</>} />
                <div className="card-body stack">
                  <p className="muted">{s.description}</p>
                  {r && (
                    <div className="row">
                      <Badge tone="safe">{r.summary.proposals} proposals</Badge>
                      <Badge tone={r.summary.projected + r.summary.rejected ? 'warn' : 'neutral'}>{r.summary.projected + r.summary.rejected} interventions</Badge>
                      <Badge tone={r.summary.violations_caused_by_actions ? 'danger' : 'safe'}>{r.summary.violations_caused_by_actions} violations caused</Badge>
                    </div>
                  )}
                  <div className="row">
                    <Button variant="primary" icon={Play} loading={isRunning} disabled={(!!busy && !isRunning) || live || (running !== null && !isRunning)} onClick={() => go(s.id)} title={live ? 'Stop the live run first' : undefined}>
                      {isRunning ? 'Running…' : r ? 'Run again' : 'Run to completion'}
                    </Button>
                    {r && <Button variant="ghost" icon={Timer} onClick={() => setOpen(s.id)}>View summary</Button>}
                  </div>
                </div>
              </Card>
            )
          })}
        </Stagger>
      )}
      <SlideUp inView><Experiment /></SlideUp>
      <Modal open={!!openScenario} onClose={() => setOpen(null)} title={openScenario ? `${openScenario.name}: run summary` : ''} footer={<Button onClick={() => setOpen(null)}>Close</Button>}>
        {openScenario && results[openScenario.id] && <KeyValueList items={summaryItems(results[openScenario.id].summary)} />}
      </Modal>
    </div>
  )
}

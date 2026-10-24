import { ExternalLink } from 'lucide-react'
import { PageHeader } from '../components/ui/AppShell'
import { Card } from '../components/ui/display'
import { ErrorState, Skeleton } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { useGet } from '../lib/useRequest'
import { CTRL_VAR } from '../format'

const ROWS = [
  { cap: 'YOLO vehicle detection', paper: 'YOLO-based light-bar detection', ours: 'YOLOv8n + HSV light-bar detector + PCU density (Vision page)' },
  { cap: 'Emergency-aware adaptive control', paper: 'Pre-emption at one junction', ours: 'Route-wide green wave via 15 s upstream look-ahead' },
  { cap: 'SUMO system-level validation', paper: 'SUMO scenarios', ours: 'Built-in pure-Python network simulator, 4 controllers on identical traffic' },
  { cap: '- (abstract extension)', paper: '-', ours: 'ML queue forecasting (gradient boosting, 30 s ahead)' },
  { cap: '- (abstract extension)', paper: '-', ours: 'Inter-junction communication: platoon look-ahead + spill-back avoidance' },
  { cap: '- (abstract extension)', paper: '-', ours: 'Red-light and wrong-way violation detection with evidence log' },
  { cap: '- (advanced)', paper: '-', ours: 'PCU-weighted pressure, fairness term, fuel/CO₂ estimates, live control centre' },
]

// Node boxes for the pipeline diagram: [id, label, x, y, tone]
const NODES = [
  ['cam', 'Camera frame', 10, 110, 'muted'],
  ['yolo', 'YOLOv8 vehicle detection', 190, 30, 'cyan'],
  ['lb', 'Light-bar emergency detector', 190, 190, 'alert'],
  ['den', 'Density (PCU)', 390, 30, 'cyan'],
  ['ml', 'ML queue forecast', 570, 30, 'info'],
  ['ctl', 'Signal controller (pressure + pre-emption)', 570, 110, 'ok'],
  ['nb', 'Neighbour junctions (green wave, spill-back)', 770, 110, 'warn'],
  ['vio', 'Violation detector', 390, 110, 'hot'],
]
const EDGES = [['cam', 'yolo'], ['cam', 'lb'], ['yolo', 'den'], ['den', 'ml'], ['ml', 'ctl'], ['lb', 'ctl'], ['ctl', 'nb'], ['yolo', 'vio']]
const W = 150
const H = 56

function Pipeline() {
  const byId = Object.fromEntries(NODES.map((n) => [n[0], n]))
  const anchor = (id, side) => {
    const [, , x, y] = byId[id]
    return side === 'r' ? [x + W, y + H / 2] : [x, y + H / 2]
  }
  return (
    <div className="-mx-4 overflow-x-auto px-4">
      <svg viewBox="0 0 940 260" className="min-w-[860px]" role="img" aria-label="System pipeline: camera frame to YOLOv8 vehicle detection and light-bar detector, density, ML forecast, signal controller, neighbour junctions; violation detector fed by YOLOv8.">
        <defs>
          <marker id="arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L8 4L0 8z" fill="var(--dim)" /></marker>
        </defs>
        {EDGES.map(([a, b]) => {
          const [x1, y1] = anchor(a, 'r')
          const [x2, y2] = anchor(b, 'l')
          const mx = (x1 + x2) / 2
          return <path key={a + b} d={`M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`} fill="none" stroke="var(--line-strong)" strokeWidth="1.5" markerEnd="url(#arr)" />
        })}
        <path d="M845 166 L845 205 L645 205 L645 168" fill="none" stroke="var(--line-strong)" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#arr)" />
        {NODES.map(([id, label, x, y, tone]) => (
          <g key={id}>
            <rect x={x} y={y} width={W} height={H} rx="6" fill="var(--panel-2)" stroke={`var(--${tone === 'muted' ? 'line-strong' : tone})`} strokeOpacity={tone === 'muted' ? 1 : 0.6} />
            <foreignObject x={x + 6} y={y + 4} width={W - 12} height={H - 8}>
              <div xmlns="http://www.w3.org/1999/xhtml" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', textAlign: 'center', fontFamily: 'JetBrains Mono Variable, monospace', fontSize: 11, lineHeight: 1.25, color: 'var(--fg)' }}>{label}</div>
            </foreignObject>
          </g>
        ))}
      </svg>
    </div>
  )
}

export default function About() {
  const meta = useGet('/meta')
  const controllers = meta.data ? Object.entries(meta.data.controllers) : []
  return (
    <div>
      <PageHeader eyebrow="06 · about" title="About the project and the base paper" />

      <Card title="Base paper">
        <p className="text-sm leading-relaxed text-muted">
          <em className="not-italic text-fg">Emergency-Aware Adaptive Traffic Signal Control Using YOLO-Based Light-Bar Detection and SUMO System-Level Validation</em>,
          IEEE Access, 2026.
        </p>
        <a href="https://doi.org/10.1109/access.2026.3710015" target="_blank" rel="noreferrer"
          className="mt-2 inline-flex items-center gap-1.5 font-mono text-sm text-ok underline-offset-4 hover:underline">
          doi:10.1109/access.2026.3710015 <ExternalLink size={13} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span>
        </a>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          The surveyed systems do adaptive signal control <strong className="text-fg">or</strong> vehicle detection separately. The gap this project closes is{' '}
          <strong className="text-fg">one pipeline</strong> that detects, adapts timing, prioritises emergency vehicles and coordinates between junctions.
        </p>
      </Card>

      <Card title="What is adopted vs. what is advanced" className="mt-4">
        <Table rows={ROWS} rowKey={(r) => r.ours} dense caption="Adopted versus advanced capabilities"
          columns={[
            { key: 'cap', label: 'Capability', render: (r) => <span className="text-fg">{r.cap}</span> },
            { key: 'paper', label: 'Base paper', render: (r) => <span className="text-muted">{r.paper}</span> },
            { key: 'ours', label: 'This implementation', render: (r) => <span>{r.ours}</span> },
          ]}
          cards={(r) => (
            <div className="rounded border border-line bg-panel-2 p-3 text-xs">
              <div className="font-mono text-fg">{r.cap}</div>
              <div className="mt-1 text-dim">Paper: {r.paper}</div>
              <div className="mt-1 text-muted">{r.ours}</div>
            </div>
          )} />
      </Card>

      <Card title="System pipeline" className="mt-4"><Pipeline /></Card>

      <Card title="Controllers" className="mt-4">
        {meta.loading && !meta.data && <Skeleton className="h-24" />}
        {meta.error && <ErrorState error={meta.error} compact onRetry={meta.reload} />}
        <ul className="grid gap-2 sm:grid-cols-2">
          {controllers.map(([k, v]) => (
            <li key={k} className="flex items-center gap-3 rounded-[6px] border border-line bg-panel-2 px-3 py-2 text-sm">
              <i className="h-2.5 w-2.5 rounded-[2px]" style={{ background: CTRL_VAR[k] }} aria-hidden="true" />
              <span className="flex-1 text-fg">{v}</span>
              <code className="font-mono text-[11px] text-dim">{k}</code>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Run it" className="mt-4">
        <pre className="overflow-x-auto rounded-[6px] border border-line bg-bg/60 p-3 font-mono text-xs leading-relaxed text-fg">{`run.bat                          # backend :8310 + frontend :5310
python scripts/smoke_test.py     # end-to-end API check`}</pre>
        <p className="mt-3 text-xs leading-relaxed text-dim">
          Vehicle speeds and flows are modelled at queue level (mesoscopic), calibrated to typical saturation flow (1800 veh/h/lane),
          12 s links, 3 s clearance and 2 s start-up lost time.
        </p>
      </Card>
    </div>
  )
}

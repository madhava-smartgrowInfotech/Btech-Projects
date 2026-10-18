import { Network } from 'lucide-react'
import { useSimulation } from '../hooks/useSimulation'
import { kw, num, pu, pctPoints } from '../lib/format'
import { PageHeader } from '../components/ui/layout'
import { Card, CardHeader, Table } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton } from '../components/ui/feedback'
import { SlideUp } from '../components/motion'

const vColor = (v) => (v < 0.95 || v > 1.05 ? 'var(--danger)' : v < 0.96 || v > 1.04 ? 'var(--warn)' : 'var(--safe)')
const lColor = (p) => (p > 100 ? 'var(--danger)' : p > 80 ? 'var(--warn)' : 'var(--info)')
const lTone = (p) => (p > 100 ? 'is-danger' : p > 80 ? 'is-warn' : '')

const CARD_W = 160
const CARD_H = 68

function Diagram({ topology, grid }) {
  const pos = Object.fromEntries(topology.nodes.map((n) => [n.id, n]))
  const buses = Object.fromEntries((grid?.buses || []).map((b) => [b.name, b]))
  const lines = Object.fromEntries((grid?.lines || []).map((l) => [l.name, l]))
  const trafo = (grid?.trafos || [])[0]
  const nodeByBus = Object.fromEntries((grid?.nodes || []).map((n) => [`B${n.bus}`, n]))
  // frame the drawing around the nodes and the device cards instead of a fixed canvas
  const busNodes = topology.nodes.filter((n) => n.type === 'bus')
  const rightOf = (n) => topology.nodes.some((o) => o.id !== n.id && o.x > n.x + 10 && Math.abs(o.y - n.y) < 24)
  const xs = topology.nodes.map((n) => n.x)
  const ys = topology.nodes.map((n) => n.y)
  const x0 = Math.min(...xs) - 70
  const x1 = Math.max(...xs) + 24 + CARD_W + 16
  const y0 = Math.min(...ys) - CARD_H - 56
  const y1 = Math.max(...ys) + 64
  return (
    <svg className="sld" viewBox={`${x0} ${y0} ${x1 - x0} ${y1 - y0}`} width="100%" role="img" aria-label="Single line diagram of the feeder: external grid, transformer, three buses and their devices">
      {topology.edges.map((e) => {
        const a = pos[e.source]
        const b = pos[e.target]
        if (!a || !b) return null
        const l = lines[e.id]
        const load = e.kind === 'trafo' ? trafo?.loading_percent : l?.loading_percent
        const mx = (a.x + b.x) / 2
        const my = (a.y + b.y) / 2
        return (
          <g key={e.id}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={load === undefined ? 'var(--border-strong)' : lColor(load)} strokeWidth={e.kind === 'trafo' ? 6 : 4} strokeLinecap="round" />
            <text className="sld-label halo" x={mx} y={my - 10} textAnchor="middle">{e.id}</text>
            <text className="sld-sub halo" x={mx} y={my + 14} textAnchor="middle">
              {load === undefined ? '' : `${num(load, 0)}% loaded`}
              {l ? `, ${num(l.p_from_kw, 1)} kW` : ''}
            </text>
          </g>
        )
      })}
      {pos.ext && (
        <g>
          <rect x={pos.ext.x - 42} y={pos.ext.y - 24} width="84" height="48" rx="8" className="sld-box" />
          <text className="sld-label" x={pos.ext.x} y={pos.ext.y - 3} textAnchor="middle">External grid</text>
          <text className="sld-sub" x={pos.ext.x} y={pos.ext.y + 14} textAnchor="middle">{grid?.totals ? kw(grid.totals.ext_grid_kw, 1) : ''}</text>
        </g>
      )}
      {busNodes.map((n) => {
        const b = buses[n.id]
        const nd = nodeByBus[n.id]
        const dev = topology.devices.find((d) => d.bus === n.id)
        return (
          <g key={n.id}>
            <circle cx={n.x} cy={n.y} r="15" className="sld-bus" stroke={b ? vColor(b.vm_pu) : 'var(--border-strong)'} strokeWidth="4" />
            <text className="sld-label" x={n.x} y={n.y + 4} textAnchor="middle" fontSize="11">{n.id}</text>
            <text className="sld-sub halo" x={n.x} y={n.y + 34} textAnchor="middle">{b ? `${pu(b.vm_pu)} pu` : ''}</text>
            {dev && (
              <g transform={rightOf(n) ? `translate(${n.x - CARD_W / 2},${n.y - CARD_H - 30})` : `translate(${n.x + 24},${n.y - 32})`}>
                <rect width={CARD_W} height={CARD_H} rx="8" className="sld-box" />
                <text className="sld-label" x="10" y="17">{dev.label}</text>
                <text className="sld-sub" x="10" y="32">{dev.devices.join(', ')}</text>
                {nd && <text className="sld-sub" x="10" y="47">load {num(nd.load_kw, 1)} / PV {num(nd.pv_kw, 1)} kW</text>}
                {nd && <text className="sld-sub" x="10" y="61">battery {num(nd.battery_kw, 1)} kW, SOC {num(nd.soc * 100, 0)}%</text>}
              </g>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export default function GridView() {
  const { topology, grid, ready, error, refresh } = useSimulation()
  const rows = [
    ...(grid?.lines || []).map((l) => ({ id: l.name, kind: 'Line', p: l.p_from_kw, i: l.i_ka, max: l.max_i_ka, loading: l.loading_percent })),
    ...((grid?.trafos || []).slice(0, 1).map((t) => ({ id: 'T0 transformer', kind: 'Transformer', p: t.p_hv_kw, i: null, max: null, loading: t.loading_percent }))),
  ]
  const columns = [
    { key: 'id', label: 'Element', render: (r) => <strong>{r.id}</strong> },
    { key: 'kind', label: 'Type', hideSm: true },
    { key: 'p', label: 'Active power', num: true, render: (r) => kw(r.p) },
    { key: 'i', label: 'Current (kA)', num: true, hideSm: true, render: (r) => (r.i == null ? '-' : num(r.i, 4)) },
    { key: 'max', label: 'Rated (kA)', num: true, hideSm: true, render: (r) => (r.max == null ? '-' : num(r.max, 4)) },
    { key: 'loading', label: 'Loading', num: true, render: (r) => <span className={`load-cell ${lTone(r.loading)}`}>{pctPoints(r.loading, 1)}</span> },
  ]
  return (
    <div className="stack">
      <PageHeader title="Grid view" description="Low-voltage feeder behind a 20/0.4 kV transformer. Line colour shows loading; bus ring colour shows voltage against the 0.95 - 1.05 pu band." />
      <SlideUp>
        <Card>
          <CardHeader
            title="Single line diagram"
            subtitle="Live from the latest power flow"
            actions={
              <div className="legend">
                <span><i style={{ background: 'var(--safe)' }} />voltage ok</span>
                <span><i style={{ background: 'var(--warn)' }} />near limit</span>
                <span><i style={{ background: 'var(--danger)' }} />violation</span>
              </div>
            }
          />
          <div className="card-body">
            {!ready ? <Skeleton height={320} radius={12} /> : topology ? <Diagram topology={topology} grid={grid} /> : error ? (
              <ErrorState title="Topology unavailable" error={new Error('The feeder layout could not be loaded from the API.')} onRetry={refresh} />
            ) : (
              <EmptyState icon={Network} title="No topology" />
            )}
          </div>
        </Card>
      </SlideUp>
      <SlideUp inView>
        <Card>
          <CardHeader title="Line and transformer loading" subtitle="Thermal loading against rated current" />
          <Table
            caption="Line and transformer loading"
            columns={columns}
            rows={rows}
            rowKey={(r) => r.id}
            pageSize={12}
            loading={!ready}
            empty={<EmptyState icon={Network} title="No power-flow result yet">Step or start the simulation to see line and transformer loading.</EmptyState>}
          />
        </Card>
      </SlideUp>
    </div>
  )
}

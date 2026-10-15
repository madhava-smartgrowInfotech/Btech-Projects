import { useMemo, useState } from 'react'
import { Network } from 'lucide-react'
import { AsyncView, CardSkeleton } from '../components/common'
import { Badge, Card, CardHeader, EmptyState, PageHeader, ProgressBar, Select } from '../components/ui'
import { STATUS } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const COLOR = {
  completed: 'var(--safe)',
  strong: 'var(--info)',
  weak: 'var(--warn)',
  recommended: 'var(--violet)',
  locked: 'var(--text-3)',
}
const W = 1000
const H = 640
const PAD = 70

function GraphView({ data, selected, onSelect }) {
  const { nodes, edges } = data
  const byId = useMemo(() => Object.fromEntries(nodes.map((n) => [n.id, n])), [nodes])
  const pos = useMemo(() => {
    const xs = nodes.map((n) => n.x)
    const ys = nodes.map((n) => n.y)
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]
    const sx = (W - PAD * 2) / (x1 - x0 || 1)
    const sy = (H - PAD * 2) / (y1 - y0 || 1)
    return Object.fromEntries(nodes.map((n) => [n.id, [PAD + (n.x - x0) * sx, PAD + (n.y - y0) * sy]]))
  }, [nodes])
  const sel = byId[selected]
  const linked = (e) => sel && (e.source === sel.id || e.target === sel.id)

  return (
    <div className="graph-wrap" tabIndex={0} role="region" aria-label="Knowledge graph, scrollable">
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Prerequisite knowledge graph. Each topic is a button; select one to see details below.">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0 0 L10 5 L0 10 z" fill="var(--text-3)" />
          </marker>
        </defs>
        {edges.map((e) => {
          const [x1, y1] = pos[e.source]
          const [x2, y2] = pos[e.target]
          const dx = x2 - x1
          const dy = y2 - y1
          const len = Math.hypot(dx, dy) || 1
          const r = 20
          return (
            <line
              key={`${e.source}-${e.target}`}
              className={`g-edge${linked(e) ? ' hl' : ''}`}
              x1={x1 + (dx / len) * r}
              y1={y1 + (dy / len) * r}
              x2={x2 - (dx / len) * (r + 4)}
              y2={y2 - (dy / len) * (r + 4)}
              markerEnd="url(#arrow)"
            />
          )
        })}
        {nodes.map((n) => {
          const [x, y] = pos[n.id]
          return (
            <g
              key={n.id}
              className={`g-node${n.id === selected ? ' sel' : ''}`}
              transform={`translate(${x} ${y})`}
              role="button"
              tabIndex={0}
              aria-pressed={n.id === selected}
              aria-label={`${n.name}: ${STATUS[n.status].label}, ${Math.round(n.proficiency)}% proficiency`}
              onClick={() => onSelect(n.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelect(n.id)
                }
              }}
            >
              <circle r={n.id === selected ? 22 : 18} fill={COLOR[n.status]} stroke="var(--panel-2)" strokeWidth="3" />
              {n.id === selected && <circle r="28" fill="none" stroke={COLOR[n.status]} strokeOpacity="0.5" strokeWidth="2" />}
              <text textAnchor="middle" y="-28">
                {n.name}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

export default function Graph() {
  const state = useAsync(() => api.get('/graph'), [])
  const [selected, setSelected] = useState(null)

  return (
    <>
      <PageHeader
        title="Knowledge graph"
        description="Your curriculum as a directed prerequisite graph: the core concept adopted from the base paper, extended with career-goal-aware roadmaps."
      />
      <AsyncView state={state} skeleton={<CardSkeleton rows={9} />}>
        {(d) => {
          if (!d.nodes.length)
            return (
              <Card>
                <EmptyState icon={Network} title="No topics found">The database has no learning topics. Restart the backend to seed it.</EmptyState>
              </Card>
            )
          const sorted = [...d.nodes].sort((a, b) => a.name.localeCompare(b.name))
          const cur = d.nodes.find((n) => n.id === (selected ?? sorted[0].id))
          return (
            <div className="stack">
              <Card>
                <CardHeader
                  title="Topic graph"
                  subtitle="Arrows point from a prerequisite to the topic it unlocks. Select a topic to explore it."
                  actions={
                    <div className="chips" aria-label="Legend">
                      {Object.entries(STATUS).map(([k, v]) => (
                        <span className="chip" key={k}>
                          <i className="swatch" style={{ background: COLOR[k], margin: 0 }} aria-hidden="true" />
                          {v.label} · {d.counts[k] || 0}
                        </span>
                      ))}
                    </div>
                  }
                />
                <div className="card-body">
                  <GraphView data={d} selected={cur.id} onSelect={setSelected} />
                </div>
              </Card>

              <Card>
                <CardHeader title="Explore a topic" />
                <div className="card-body split">
                  <div className="stack" style={{ gap: 14 }}>
                    <div style={{ maxWidth: 360 }}>
                      <Select
                        label="Select a topic"
                        value={String(cur.id)}
                        onChange={(e) => setSelected(Number(e.target.value))}
                        options={sorted.map((n) => ({ value: String(n.id), label: n.name }))}
                      />
                    </div>
                    <div>
                      <div className="row">
                        <h3 style={{ fontSize: 22 }}>{cur.name}</h3>
                        <Badge tone={STATUS[cur.status].tone} dot>
                          {STATUS[cur.status].label}
                        </Badge>
                      </div>
                      <p className="muted" style={{ marginTop: 8 }}>{cur.description}</p>
                    </div>
                    <ProgressBar value={cur.proficiency} max={100} label="Current proficiency" valueLabel={`${Math.round(cur.proficiency)}%`} />
                    <div className="meta-line">
                      <span>Difficulty: {cur.difficulty}</span>
                      <span>Estimated time: {Math.round(cur.estimated_hours)} hours</span>
                    </div>
                  </div>
                  <div className="stack" style={{ gap: 14 }}>
                    <div>
                      <strong>Prerequisites</strong>
                      {cur.prerequisites.length ? (
                        <ul className="bullets">{cur.prerequisites.map((p) => <li key={p}>{p}</li>)}</ul>
                      ) : (
                        <p className="faint">None. This is a starting topic.</p>
                      )}
                    </div>
                    <div>
                      <strong>Next topics it unlocks</strong>
                      {cur.next_topics.length ? (
                        <ul className="bullets">{cur.next_topics.slice(0, 5).map((p) => <li key={p}>{p}</li>)}</ul>
                      ) : (
                        <p className="faint">None. This is a terminal topic.</p>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          )
        }}
      </AsyncView>
    </>
  )
}

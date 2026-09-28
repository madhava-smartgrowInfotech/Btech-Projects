import { useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useNavigate } from 'react-router-dom'
import { inr, riskColor } from '../format'

// Interactive buyer-seller graph: node colour = risk, red animated links = circular-trading loop edges.
export default function GraphView({ data, height = 480 }) {
  const wrap = useRef(null)
  const fg = useRef(null)
  const [width, setWidth] = useState(600)
  const [hover, setHover] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(() => setWidth(el.clientWidth))
    ro.observe(el)
    setWidth(el.clientWidth)
    return () => ro.disconnect()
  }, [])

  const graph = useMemo(() => {
    if (!data) return { nodes: [], links: [] }
    const maxV = Math.max(1, ...data.links.map((l) => l.value))
    return {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.links.map((l) => ({ ...l, w: 0.5 + 3.5 * Math.sqrt(l.value / maxV) })),
    }
  }, [data])

  useEffect(() => {
    // spread larger networks out so loops and clusters are readable
    fg.current?.d3Force('charge')?.strength(graph.nodes.length > 60 ? -90 : -60)
    fg.current?.d3ReheatSimulation()
  }, [graph])

  return (
    <div ref={wrap} className="relative w-full rounded-lg border border-slate-200 bg-slate-50 overflow-hidden" style={{ height }}>
      {graph.nodes.length === 0 ? (
        <div className="flex h-full items-center justify-center text-sm text-slate-500">Nothing to show for this selection.</div>
      ) : (
        <ForceGraph2D
          ref={fg}
          width={width}
          height={height}
          graphData={graph}
          cooldownTicks={150}
          onEngineStop={() => fg.current?.zoomToFit(400, 40)}
          nodeRelSize={4}
          nodeVal={(n) => (n.focus ? 4 : 1 + n.risk * 2.5)}
          linkColor={(l) => (l.ring ? '#dc2626' : 'rgba(100,116,139,0.35)')}
          linkWidth={(l) => (l.ring ? Math.max(2, l.w) : l.w)}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={0.9}
          linkDirectionalParticles={(l) => (l.ring ? 3 : 0)}
          linkDirectionalParticleWidth={2.5}
          linkDirectionalParticleColor={() => '#dc2626'}
          onNodeHover={setHover}
          onNodeClick={(n) => navigate(`/app/taxpayers/${n.id}`)}
          nodeCanvasObjectMode={() => 'after'}
          nodeCanvasObject={(n, ctx, scale) => {
            const r = Math.sqrt(n.focus ? 4 : 1 + n.risk * 2.5) * 4
            ctx.beginPath()
            ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
            ctx.fillStyle = riskColor(n.risk)
            ctx.fill()
            if (n.focus || n.cluster) {
              ctx.lineWidth = 2 / scale
              ctx.strokeStyle = n.focus ? '#1e1b4b' : '#7c3aed'
              ctx.setLineDash(n.cluster && !n.focus ? [3 / scale, 2 / scale] : [])
              ctx.stroke()
              ctx.setLineDash([])
            }
            if (scale > 1.4 || n.focus) {
              ctx.font = `${11 / scale}px sans-serif`
              ctx.fillStyle = '#0f172a'
              ctx.textAlign = 'center'
              ctx.fillText(n.name, n.x, n.y + r + 10 / scale)
            }
          }}
          linkLabel={(l) => `${inr(l.value)} · ${l.count} invoices · ${l.months} months${l.ring ? ' · ring edge' : ''}`}
        />
      )}
      {hover && (
        <div className="absolute top-2 left-2 max-w-xs rounded-lg bg-white/95 border border-slate-200 shadow p-2.5 text-xs pointer-events-none">
          <div className="font-semibold text-slate-800">{hover.name}</div>
          <div className="text-slate-500 font-mono">{hover.id}</div>
          <div className="mt-1">Risk <b style={{ color: riskColor(hover.risk) }}>{hover.risk.toFixed(2)}</b> · {hover.sector}</div>
          {hover.rings.length > 0 && <div className="text-red-600">Ring {hover.rings.join(', ')}</div>}
          {hover.cluster && <div className="text-violet-600">Shared-identity cluster {hover.cluster}</div>}
          <div className="text-slate-400 mt-1">Click to open profile</div>
        </div>
      )}
      <div className="absolute bottom-2 right-2 flex flex-wrap gap-3 rounded-md bg-white/90 border border-slate-200 px-2 py-1 text-[11px] text-slate-600">
        <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-full bg-red-600 inline-block" />high risk</span>
        <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-full bg-green-600 inline-block" />low risk</span>
        <span className="flex items-center gap-1"><i className="w-4 h-0.5 bg-red-600 inline-block" />loop edge</span>
        <span className="flex items-center gap-1"><i className="w-2.5 h-2.5 rounded-full border-2 border-dashed border-violet-600 inline-block" />shared identity</span>
      </div>
    </div>
  )
}

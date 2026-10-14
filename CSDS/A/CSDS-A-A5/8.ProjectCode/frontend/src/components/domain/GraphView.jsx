import { Maximize2, Minus, Plus } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { inr, riskTone, SECTORS } from '../../format'
import { useReducedMotion, useSize } from '../../lib/reduced'
import { useTheme } from '../../lib/theme'
import { IconButton } from '../ui/controls'
import { EmptyState, Skeleton } from '../ui/feedback'

const ForceGraph2D = lazy(() => import('react-force-graph-2d'))

// Interactive buyer-seller graph: node colour = risk band, red animated links = circular-trading loop edges.
export default function GraphView({ data, height = 480 }) {
  const wrap = useRef(null)
  const fg = useRef(null)
  const { width } = useSize(wrap)
  const [hover, setHover] = useState(null)
  const navigate = useNavigate()
  const { tokens } = useTheme()
  const reduced = useReducedMotion()

  const graph = useMemo(() => {
    if (!data) return { nodes: [], links: [] }
    const maxV = Math.max(1, ...data.links.map((l) => l.value))
    return {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.links.map((l) => ({ ...l, w: 0.4 + 3 * Math.sqrt(l.value / maxV) })),
    }
  }, [data])

  useEffect(() => {
    fg.current?.d3Force('charge')?.strength(graph.nodes.length > 60 ? -90 : -60)
    fg.current?.d3ReheatSimulation?.()
  }, [graph, width])

  const zoom = (f) => fg.current && fg.current.zoom(fg.current.zoom() * f, 300)
  const nodeR = (n) => Math.sqrt(n.focus ? 4 : 1 + n.risk * 2.5) * 4

  return (
    <div ref={wrap} className="grid-bg relative w-full overflow-hidden rounded-[6px] border border-line bg-bg/60" style={{ height }}>
      {graph.nodes.length === 0 ? (
        <EmptyState title="Nothing to draw" body="This selection has no trading links in the current ecosystem." className="h-full" />
      ) : width > 0 && (
        <Suspense fallback={<Skeleton className="h-full w-full" />}>
          <ForceGraph2D
            ref={fg}
            width={width}
            height={height}
            graphData={graph}
            backgroundColor="rgba(0,0,0,0)"
            cooldownTicks={reduced ? 60 : 150}
            onEngineStop={() => fg.current?.zoomToFit(400, 40)}
            nodeRelSize={4}
            nodeVal={(n) => (n.focus ? 4 : 1 + n.risk * 2.5)}
            linkColor={(l) => (l.ring ? tokens.alert : tokens.lineStrong)}
            linkWidth={(l) => (l.ring ? Math.max(1.6, l.w) : l.w)}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={0.92}
            linkDirectionalArrowColor={(l) => (l.ring ? tokens.alert : tokens.dim)}
            linkDirectionalParticles={(l) => (l.ring && !reduced ? 3 : 0)}
            linkDirectionalParticleWidth={2.2}
            linkDirectionalParticleColor={() => tokens.alert}
            onNodeHover={(n) => { setHover(n); if (wrap.current) wrap.current.style.cursor = n ? 'pointer' : '' }}
            onNodeClick={(n) => navigate(`/app/taxpayers/${n.id}`)}
            nodeCanvasObjectMode={() => 'replace'}
            nodeCanvasObject={(n, ctx, scale) => {
              const r = nodeR(n)
              const c = tokens[riskTone(n.risk)]
              ctx.beginPath()
              ctx.arc(n.x, n.y, r, 0, 2 * Math.PI)
              ctx.fillStyle = c
              ctx.globalAlpha = 0.9
              ctx.fill()
              ctx.globalAlpha = 1
              ctx.lineWidth = 1 / scale
              ctx.strokeStyle = tokens.bg
              ctx.stroke()
              if (n.focus || n.cluster) {
                ctx.beginPath()
                ctx.arc(n.x, n.y, r + 2.5 / scale + 1, 0, 2 * Math.PI)
                ctx.lineWidth = 1.5 / scale
                ctx.strokeStyle = n.focus ? tokens.fg : tokens.info
                ctx.setLineDash(n.cluster && !n.focus ? [3 / scale, 2 / scale] : [])
                ctx.stroke()
                ctx.setLineDash([])
              }
              if (scale > 1.5 || n.focus) {
                ctx.font = `${10.5 / scale}px "JetBrains Mono", monospace`
                ctx.fillStyle = tokens.fg
                ctx.textAlign = 'center'
                ctx.fillText(n.name, n.x, n.y + r + 10 / scale)
              }
            }}
            nodePointerAreaPaint={(n, color, ctx) => {
              ctx.fillStyle = color
              ctx.beginPath()
              ctx.arc(n.x, n.y, nodeR(n) + 2, 0, 2 * Math.PI)
              ctx.fill()
            }}
            linkLabel={(l) => `${inr(l.value)} · ${l.count} invoices · ${l.months} months${l.ring ? ' · loop edge' : ''}`}
          />
        </Suspense>
      )}
      {hover && (
        <div className="pointer-events-none absolute left-2 top-2 max-w-[260px] rounded-[6px] border border-line-strong bg-panel/95 p-2.5 font-mono text-[11px] shadow-xl">
          <div className="font-sans text-sm font-medium text-fg">{hover.name}</div>
          <div className="text-dim">{hover.id}</div>
          <div className="mt-1 text-muted">risk <b style={{ color: `var(--${riskTone(hover.risk)})` }}>{hover.risk.toFixed(2)}</b> · {SECTORS[hover.sector] || hover.sector}</div>
          {hover.rings.length > 0 && <div className="text-alert">loop {hover.rings.join(', ')}</div>}
          {hover.cluster && <div className="text-info">shared-identity cluster {hover.cluster}</div>}
          <div className="mt-1 text-dim">click → profile</div>
        </div>
      )}
      {graph.nodes.length > 0 && (
        <>
          <div className="absolute right-2 top-2 flex flex-col gap-1 rounded-[6px] border border-line bg-panel/90 p-0.5">
            <IconButton size="sm" icon={Plus} label="Zoom in" onClick={() => zoom(1.4)} />
            <IconButton size="sm" icon={Minus} label="Zoom out" onClick={() => zoom(1 / 1.4)} />
            <IconButton size="sm" icon={Maximize2} label="Fit to view" onClick={() => fg.current?.zoomToFit(400, 40)} />
          </div>
          <div className="absolute bottom-2 left-2 flex flex-wrap gap-x-3 gap-y-1 rounded-[6px] border border-line bg-panel/90 px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted">
            <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-alert" />high risk</span>
            <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-warn" />watch</span>
            <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-ok" />low</span>
            <span className="flex items-center gap-1"><i className="inline-block w-3 border-t-2 border-alert" />loop edge</span>
            <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full border border-dashed border-info" />shared identity</span>
          </div>
        </>
      )}
      <span className="sr-only">{`Trading network with ${graph.nodes.length} taxpayers and ${graph.links.length} links. The same taxpayers are listed in the tables on this page.`}</span>
    </div>
  )
}

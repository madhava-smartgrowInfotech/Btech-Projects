// Interactive node-link view (canvas). Loaded lazily - the library is only fetched on screens that draw a graph.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useReducedMotion } from 'framer-motion'
import ForceGraph2D from 'react-force-graph-2d'
import { useChartTheme } from '../../lib/palette'

export default function ForceGraph({ nodes, links, onNodeClick, height = 420, label, threshold = 0.5 }) {
  const t = useChartTheme()
  const reduce = useReducedMotion()
  const box = useRef(null)
  const fg = useRef(null)
  const [w, setW] = useState(640)
  const data = useMemo(() => ({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) }), [nodes, links])

  useEffect(() => {
    const el = box.current
    if (!el) return undefined
    const ro = new ResizeObserver(() => setW(Math.max(260, el.clientWidth)))
    ro.observe(el)
    setW(Math.max(260, el.clientWidth))
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    const f = fg.current
    if (!f) return
    f.d3Force('charge')?.strength(-46)
    f.d3Force('link')?.distance(34)
  }, [data])

  const color = (n) => (n.score >= threshold ? t.rose : n.score >= 0.3 ? t.peach : t.mint)

  return (
    <div ref={box} className="graph-box" style={{ height }} role="img" aria-label={label}>
      <ForceGraph2D
        ref={fg}
        graphData={data}
        width={w}
        height={height}
        backgroundColor="rgba(0,0,0,0)"
        nodeRelSize={4}
        nodeVal={(n) => (n.ego ? 5 : 1 + Math.min(2, Math.log10(n.degree + 1) / 2))}
        nodeColor={color}
        nodeLabel={(n) => `${n.handle} · ${Math.round(n.score * 100)}% fake · ${n.degree} ties`}
        linkColor={(l) => (l.injected ? t.rose : t.grid)}
        linkWidth={(l) => (l.injected ? 1.2 : 0.7)}
        linkDirectionalParticles={0}
        cooldownTicks={reduce ? 0 : 120}
        warmupTicks={reduce ? 140 : 20}
        onNodeClick={onNodeClick}
        nodeCanvasObjectMode={(n) => (n.ego ? 'after' : undefined)}
        nodeCanvasObject={(n, ctx) => {
          ctx.beginPath()
          ctx.arc(n.x, n.y, 9, 0, 2 * Math.PI)
          ctx.lineWidth = 2
          ctx.strokeStyle = t.text
          ctx.stroke()
        }}
        enableNodeDrag={!reduce}
        onEngineStop={() => fg.current?.zoomToFit(reduce ? 0 : 400, 36)}
      />
    </div>
  )
}

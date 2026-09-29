import { useEffect, useRef } from 'react'

const EDGES = [[5, 6], [5, 7], [7, 9], [6, 8], [8, 10], [5, 11], [6, 12], [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [0, 5], [0, 6]]
const VIS = 0.3

// Privacy view: draws only the body skeleton - no camera image ever reaches the browser.
export default function Skeleton({ keypoints, width = 640, height = 480, color = '#2dd4bf' }) {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current
    if (!c) return
    const ctx = c.getContext('2d')
    const W = c.width
    const H = c.height
    ctx.fillStyle = '#0f172a'
    ctx.fillRect(0, 0, W, H)
    ctx.strokeStyle = '#1e293b'
    ctx.lineWidth = 1
    for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke() }
    for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke() }
    if (!keypoints || !keypoints.length) return
    const p = keypoints.map(([x, y, s]) => [x * W, y * H, s])
    ctx.strokeStyle = color
    ctx.lineWidth = 4
    ctx.lineCap = 'round'
    for (const [a, b] of EDGES) {
      if (p[a][2] > VIS && p[b][2] > VIS) {
        ctx.beginPath(); ctx.moveTo(p[a][0], p[a][1]); ctx.lineTo(p[b][0], p[b][1]); ctx.stroke()
      }
    }
    ctx.fillStyle = '#f8fafc'
    for (const [x, y, s] of p) {
      if (s > VIS) { ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill() }
    }
    if (p[0][2] > VIS) { // head
      ctx.strokeStyle = color
      ctx.lineWidth = 3
      ctx.beginPath(); ctx.arc(p[0][0], p[0][1], 14, 0, Math.PI * 2); ctx.stroke()
    }
  }, [keypoints, width, height, color])
  return <canvas ref={ref} width={width} height={height} className="w-full h-auto rounded-lg bg-slate-900" />
}

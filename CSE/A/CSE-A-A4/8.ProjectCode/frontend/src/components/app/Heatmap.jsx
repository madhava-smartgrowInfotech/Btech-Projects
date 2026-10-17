import { useId } from 'react'

/** Diverging heatmap of a square matrix: lavender = positive, rose = negative, centred on zero. */
export default function Heatmap({ matrix, label }) {
  const id = useId()
  const n = matrix.length
  const max = Math.max(...matrix.flat().map(Math.abs)) || 1
  const cell = 10
  return (
    <svg className="heat" viewBox={`0 0 ${n * cell} ${n * cell}`} role="img" aria-label={label} aria-describedby={id}>
      <desc id={id}>{`${n} by ${n} grid. Lavender cells are positive weights, rose cells negative; stronger colour means larger magnitude.`}</desc>
      {matrix.map((row, i) =>
        row.map((v, j) => {
          const a = Math.min(1, Math.abs(v) / max)
          return (
            <rect
              key={`${i}-${j}`}
              x={j * cell}
              y={i * cell}
              width={cell}
              height={cell}
              rx={1.5}
              style={{ fill: v >= 0 ? 'var(--lavender)' : 'var(--rose)', opacity: v === 0 ? 0.06 : 0.15 + a * 0.85 }}
            >
              <title>{`Q[${i}][${j}] = ${v.toFixed(5)}`}</title>
            </rect>
          )
        }),
      )}
    </svg>
  )
}

import { useState } from 'react'
import { CHART } from './ui.jsx'

/**
 * Diverging horizontal bars around a zero baseline.
 * rows: [{ key, label, sub, value, display }]; blue = positive, red = negative.
 * Every value is also printed as signed text, so color never carries meaning alone.
 */
export function DivergingBars({ rows, posLabel, negLabel, format = (v) => v.toFixed(3) }) {
  const [hover, setHover] = useState(null)
  const max = Math.max(...rows.map((r) => Math.abs(r.value)), 1e-9)
  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-4 text-xs text-slate-600">
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CHART.blue }} /> {posLabel}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: CHART.red }} /> {negLabel}
        </span>
      </div>
      <div className="space-y-1.5">
        {rows.map((r) => {
          const w = (Math.abs(r.value) / max) * 50
          const pos = r.value >= 0
          return (
            <div
              key={r.key}
              className={`grid grid-cols-[minmax(0,11rem)_minmax(0,1fr)_4.5rem] items-center gap-2 rounded px-1 py-0.5 text-xs ${hover === r.key ? 'bg-slate-50' : ''}`}
              onMouseEnter={() => setHover(r.key)}
              onMouseLeave={() => setHover(null)}
              title={`${r.label}${r.sub ? ` (${r.sub})` : ''}: ${r.display ?? format(r.value)}`}
            >
              <div className="min-w-0">
                <div className="truncate font-medium text-slate-800">{r.label}</div>
                {r.sub && <div className="truncate text-[11px] text-slate-500">{r.sub}</div>}
              </div>
              <div className="relative h-4">
                <div className="absolute inset-y-0 left-1/2 w-px" style={{ background: CHART.axis }} />
                <div
                  className="absolute top-0.5 h-3"
                  style={{
                    background: pos ? CHART.blue : CHART.red,
                    width: `${Math.max(w, 0.8)}%`,
                    left: pos ? '50%' : `${50 - w}%`,
                    borderRadius: pos ? '0 4px 4px 0' : '4px 0 0 4px',
                  }}
                />
              </div>
              <div className="text-right font-mono tabular-nums text-slate-700">{r.display ?? format(r.value)}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function CategoryWords({ words, category }) {
  if (!words?.length) return <p className="text-xs text-slate-500">No explanation available.</p>
  return (
    <DivergingBars
      rows={words.map((w, i) => ({ key: i, label: w.word, value: w.weight, display: (w.weight >= 0 ? '+' : '') + w.weight.toFixed(3) }))}
      posLabel={`supports “${category}”`}
      negLabel="points to another category"
    />
  )
}

export function PriorityFactors({ data }) {
  if (!data?.factors?.length) return null
  return (
    <DivergingBars
      rows={data.factors.map((f) => ({ key: f.factor, label: f.factor, sub: f.value, value: f.impact, display: (f.impact >= 0 ? '+' : '') + f.impact.toFixed(2) }))}
      posLabel={`pushes toward ${data.target}`}
      negLabel={`pushes away from ${data.target}`}
    />
  )
}

export function TimeFactors({ data }) {
  if (!data?.factors?.length) return null
  return (
    <div>
      <p className="mb-2 text-xs text-slate-600">
        Typical request: <b>{data.baseline_days} days</b>. Each factor adds or removes days from that baseline.
      </p>
      <DivergingBars
        rows={data.factors.map((f) => ({ key: f.factor, label: f.factor, sub: f.value, value: f.impact, display: `${f.impact >= 0 ? '+' : ''}${f.impact.toFixed(1)} d` }))}
        posLabel="adds time"
        negLabel="saves time"
      />
    </div>
  )
}

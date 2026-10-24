import { useId } from 'react'
import { Label } from './controls'

// Labelled range slider in the kit's mono style. `format` renders the current value next to the label.
export default function RangeField({ label, value, min, max, step = 1, onChange, onCommit, format = (v) => v, disabled, hint, className = '' }) {
  const id = useId()
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div className={className}>
      <div className="mb-1.5 flex items-baseline justify-between gap-2">
        <Label htmlFor={id}>{label}</Label>
        <output htmlFor={id} className="font-mono text-sm tabular-nums text-ok">{format(value)}</output>
      </div>
      <input id={id} type="range" min={min} max={max} step={step} value={value} disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        onPointerUp={(e) => onCommit?.(Number(e.currentTarget.value))}
        onKeyUp={(e) => onCommit?.(Number(e.currentTarget.value))}
        onBlur={(e) => onCommit?.(Number(e.currentTarget.value))}
        aria-valuetext={String(format(value))}
        style={{ background: `linear-gradient(to right, var(--ok) ${pct}%, var(--line-strong) ${pct}%)` }}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full disabled:cursor-not-allowed disabled:opacity-50
          [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-[3px]
          [&::-webkit-slider-thumb]:border [&::-webkit-slider-thumb]:border-ok [&::-webkit-slider-thumb]:bg-panel
          [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:rounded-[3px] [&::-moz-range-thumb]:border [&::-moz-range-thumb]:border-ok [&::-moz-range-thumb]:bg-panel" />
      {hint && <p className="mt-1 text-xs text-dim">{hint}</p>}
    </div>
  )
}

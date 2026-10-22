import { useId, useRef } from 'react'
import { Link } from 'react-router-dom'
import { Check, X } from 'lucide-react'

/** Accessible tabs (roving focus with arrow keys). tabs: [{id, label, icon}] */
export function Tabs({ tabs, value, onChange, label }) {
  const base = useId()
  const refs = useRef([])
  const onKey = (e, i) => {
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (!dir) return
    e.preventDefault()
    const n = (i + dir + tabs.length) % tabs.length
    onChange(tabs[n].id)
    refs.current[n]?.focus()
  }
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map((t, i) => {
        const Icon = t.icon
        const sel = t.id === value
        return (
          <button
            key={t.id}
            ref={(el) => (refs.current[i] = el)}
            role="tab"
            id={`${base}-${t.id}`}
            aria-selected={sel}
            tabIndex={sel ? 0 : -1}
            className="tab"
            onClick={() => onChange(t.id)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {Icon && <Icon size={16} aria-hidden="true" />}
            {t.label}
            {t.count !== undefined && <span className="badge">{t.count}</span>}
          </button>
        )
      })}
    </div>
  )
}

export function Breadcrumbs({ items }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="crumbs">
        {items.map((it, i) => (
          <li key={i}>{it.to && i < items.length - 1 ? <Link to={it.to}>{it.label}</Link> : <span aria-current="page">{it.label}</span>}</li>
        ))}
      </ol>
    </nav>
  )
}

/** steps: string[]; current: index; failed: index that failed (optional) */
export function Stepper({ steps, current, failed, label = 'Progress' }) {
  return (
    <ol className="stepper" style={{ '--n': steps.length }} aria-label={label}>
      {steps.map((s, i) => {
        const state = i === failed ? 'failed' : i < current ? 'done' : i === current ? 'current' : ''
        return (
          <li key={s} className={`step ${state}`} aria-current={i === current ? 'step' : undefined}>
            <span className="step-num" aria-hidden="true">
              {state === 'done' ? <Check size={14} strokeWidth={3} /> : state === 'failed' ? <X size={14} strokeWidth={3} /> : i + 1}
            </span>
            <span className="step-name">
              {s}
              <span className="sr-only">{state === 'done' ? ' (done)' : state === 'current' ? ' (current)' : state === 'failed' ? ' (failed)' : ''}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}

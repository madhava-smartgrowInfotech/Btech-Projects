import { motion } from 'framer-motion'
import { Check, ChevronRight, X } from 'lucide-react'
import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { useReducedMotion } from '../../lib/reduced'

export function TabPanel({ tabsId = 'tabs', value, children, className = '' }) {
  return (
    <div role="tabpanel" id={`${tabsId}-${value}-panel`} aria-labelledby={`${tabsId}-${value}`} tabIndex={0} className={`outline-none ${className}`}>
      {children}
    </div>
  )
}

// Accessible tabs: arrow keys / Home / End move between tabs.
export function Tabs({ id = 'tabs', tabs, value, onChange, label = 'Sections' }) {
  const base = id
  const refs = useRef([])
  const reduced = useReducedMotion()
  function key(e, i) {
    const n = tabs.length
    const next = { ArrowRight: (i + 1) % n, ArrowLeft: (i - 1 + n) % n, Home: 0, End: n - 1 }[e.key]
    if (next === undefined) return
    e.preventDefault()
    refs.current[next]?.focus()
    onChange(tabs[next].id)
  }
  return (
    <div role="tablist" aria-label={label} className="-mx-1 flex gap-1 overflow-x-auto border-b border-line px-1">
      {tabs.map((t, i) => {
        const on = t.id === value
        return (
          <button key={t.id} ref={(el) => { refs.current[i] = el }} role="tab" type="button" id={`${base}-${t.id}`}
            aria-selected={on} aria-controls={`${base}-${t.id}-panel`} tabIndex={on ? 0 : -1}
            onClick={() => onChange(t.id)} onKeyDown={(e) => key(e, i)}
            className={`relative whitespace-nowrap px-3 py-2.5 font-mono text-[11px] uppercase tracking-[0.12em] transition-colors ${on ? 'text-ok' : 'text-muted hover:text-fg'}`}>
            {t.label}
            {t.count !== undefined && <span className="ml-1.5 text-dim">{t.count}</span>}
            {on && <motion.span layoutId={reduced ? undefined : `${base}-ink`} className="absolute inset-x-1 -bottom-px h-[2px] bg-ok" />}
          </button>
        )
      })}
    </div>
  )
}

export function Breadcrumbs({ items }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-dim">
        {items.map((it, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight size={12} aria-hidden="true" />}
            {it.to && i < items.length - 1 ? <Link to={it.to} className="hover:text-ok">{it.label}</Link>
              : <span aria-current={i === items.length - 1 ? 'page' : undefined} className="max-w-[40vw] truncate text-muted">{it.label}</span>}
          </li>
        ))}
      </ol>
    </nav>
  )
}

// steps: [{id, label}], current: id of the active step, done: all complete, failed: active step failed
export function Stepper({ steps, current, done = false, failed = false }) {
  const idx = done ? steps.length : Math.max(0, steps.findIndex((s) => s.id === current))
  return (
    <ol className="grid grid-cols-4 gap-x-2 gap-y-3 sm:grid-cols-8" aria-label="Pipeline stages">
      {steps.map((s, i) => {
        const state = i < idx ? 'done' : i === idx ? (failed ? 'failed' : 'active') : 'todo'
        const color = { done: 'var(--ok)', active: 'var(--warn)', failed: 'var(--alert)', todo: 'var(--line-strong)' }[state]
        return (
          <li key={s.id} className="min-w-0" aria-current={state === 'active' ? 'step' : undefined}>
            <div className="mb-1.5 h-[3px] rounded-full" style={{ background: color }} />
            <div className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider" style={{ color: state === 'todo' ? 'var(--dim)' : color }}>
              {state === 'done' ? <Check size={11} aria-hidden="true" /> : state === 'failed' ? <X size={11} aria-hidden="true" />
                : <span className={`inline-block h-1.5 w-1.5 rounded-full ${state === 'active' ? 'dot-live' : ''}`} style={{ background: color }} aria-hidden="true" />}
              <span className="truncate">{s.label}</span>
              <span className="sr-only"> ({state})</span>
            </div>
          </li>
        )
      })}
    </ol>
  )
}

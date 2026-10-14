import { useId, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Check, ChevronRight } from 'lucide-react'

const cx = (...c) => c.filter(Boolean).join(' ')

// Accessible tabs: roving arrow-key focus, animated active pill.
export function Tabs({ tabs, value, onChange, label }) {
  const group = useId()
  const refs = useRef([])
  const onKey = (e, i) => {
    const dir = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
    if (!dir) return
    e.preventDefault()
    const next = (i + dir + tabs.length) % tabs.length
    onChange(tabs[next].value)
    refs.current[next]?.focus()
  }
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map((t, i) => {
        const active = t.value === value
        return (
          <button
            key={t.value}
            ref={(el) => (refs.current[i] = el)}
            role="tab"
            id={`${group}-tab-${t.value}`}
            aria-selected={active}
            aria-controls={`${group}-panel`}
            tabIndex={active ? 0 : -1}
            className="tab"
            onClick={() => onChange(t.value)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {active && <motion.span layoutId={`pill-${group}`} className="tab-pill" transition={{ type: 'spring', stiffness: 420, damping: 34 }} />}
            <span>
              {t.icon && <t.icon size={15} aria-hidden="true" />}
              {t.label}
            </span>
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
        {items.map((it, i) => {
          const last = i === items.length - 1
          return (
            <li key={it.label} className="row" style={{ gap: 6 }}>
              {last || !it.to ? (
                <span aria-current={last ? 'page' : undefined}>{it.label}</span>
              ) : (
                <Link to={it.to}>{it.label}</Link>
              )}
              {!last && <ChevronRight size={13} aria-hidden="true" />}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

export function Stepper({ steps, current }) {
  return (
    <ol className="stepper" aria-label="Progress">
      {steps.map((s, i) => {
        const state = i < current ? 'done' : i === current ? 'current' : 'todo'
        return (
          <li key={s} className={cx('step', state)} aria-current={state === 'current' ? 'step' : undefined}>
            <span className="step-num">{state === 'done' ? <Check size={14} aria-hidden="true" /> : i + 1}</span>
            <span className="step-text">
              {s}
              {state === 'done' && <span className="sr-only"> (completed)</span>}
            </span>
            {i < steps.length - 1 && <span className="step-line" aria-hidden="true" />}
          </li>
        )
      })}
    </ol>
  )
}

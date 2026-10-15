import { useId, useRef } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Check, ChevronRight } from 'lucide-react'
import { spring } from '../../lib/motion'

/** tabs: [{id, label, icon}] - arrow keys move between tabs. */
export function Tabs({ tabs, value, onChange, label = 'Sections', name = 'tabs' }) {
  const refs = useRef([])
  const base = useId()
  const onKey = (e, i) => {
    let j = null
    if (e.key === 'ArrowRight') j = (i + 1) % tabs.length
    if (e.key === 'ArrowLeft') j = (i - 1 + tabs.length) % tabs.length
    if (e.key === 'Home') j = 0
    if (e.key === 'End') j = tabs.length - 1
    if (j != null) {
      e.preventDefault()
      onChange(tabs[j].id)
      refs.current[j]?.focus()
    }
  }
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {tabs.map((t, i) => {
        const on = t.id === value
        const Icon = t.icon
        return (
          <motion.button
            key={t.id}
            ref={(el) => (refs.current[i] = el)}
            type="button"
            role="tab"
            id={`${base}-${t.id}`}
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            className="tab"
            onClick={() => onChange(t.id)}
            onKeyDown={(e) => onKey(e, i)}
            whileTap={{ scale: 0.95 }}
            transition={spring}
          >
            {on && <motion.span layoutId={`tab-${name}`} className="seg-pill" transition={spring} />}
            <span>
              {Icon && <Icon size={16} aria-hidden="true" />}
              {t.label}
            </span>
          </motion.button>
        )
      })}
    </div>
  )
}

/** items: [{label, to}] - last item is the current page. */
export function Breadcrumbs({ items }) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="breadcrumbs" style={{ listStyle: 'none', padding: 0 }}>
        {items.map((it, i) => {
          const last = i === items.length - 1
          return (
            <li key={it.label} className="row" style={{ '--gap': '6px' }}>
              {last ? <span aria-current="page">{it.label}</span> : <Link to={it.to}>{it.label}</Link>}
              {!last && <ChevronRight size={14} aria-hidden="true" />}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

/** steps: [{label, hint}], current: index of the active step (steps before it are done). */
export function Stepper({ steps, current, label = 'Progress' }) {
  return (
    <ol className="stepper" aria-label={label}>
      {steps.map((s, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : ''
        return (
          <motion.li
            key={s.label}
            className={`step ${state}`}
            aria-current={i === current ? 'step' : undefined}
            layout
            transition={spring}
          >
            <motion.span className="step-n" animate={{ scale: state === 'active' ? [1, 1.12, 1] : 1 }} transition={spring}>
              {state === 'done' ? <Check size={15} strokeWidth={3} aria-hidden="true" /> : i + 1}
            </motion.span>
            <span className="step-text">
              {s.label}
              {s.hint && <small>{s.hint}</small>}
            </span>
          </motion.li>
        )
      })}
    </ol>
  )
}

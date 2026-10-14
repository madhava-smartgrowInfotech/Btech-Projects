import { motion } from 'framer-motion'
import { softSpring } from '../../lib/motion'

/** tone: lavender | mint | peach | sky | rose | neutral */
export function Badge({ tone = 'neutral', dot, icon: Icon, children, ...rest }) {
  return (
    <span className={`badge ${tone}`} {...rest}>
      {dot && <span className="dot" aria-hidden="true" />}
      {Icon && <Icon size={13} aria-hidden="true" />}
      {children}
    </span>
  )
}

const DOT = { lavender: 'var(--lavender)', mint: 'var(--mint)', peach: 'var(--peach)', sky: 'var(--sky)', rose: 'var(--rose)' }

/** items: [{id, title, meta, icon, tone, extra}] */
export function Timeline({ items, animate = true }) {
  return (
    <ol className="timeline">
      {items.map((it, i) => {
        const Icon = it.icon
        return (
          <motion.li
            key={it.id ?? i}
            className="tl-item"
            initial={animate ? { opacity: 0, x: -12 } : false}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ ...softSpring, delay: Math.min(i * 0.05, 0.4) }}
          >
            <span className="tl-dot" style={{ background: DOT[it.tone] || 'var(--surface-3)' }} aria-hidden="true">
              {Icon ? <Icon size={17} /> : <span className="num tiny" style={{ fontWeight: 700 }}>{i + 1}</span>}
            </span>
            <div className="tl-body">
              <div className="tl-title">{it.title}</div>
              {it.meta && <div className="tl-meta">{it.meta}</div>}
              {it.extra && <div style={{ marginTop: 8 }}>{it.extra}</div>}
            </div>
          </motion.li>
        )
      })}
    </ol>
  )
}

/** items: [[label, value], ...] */
export function KeyValueList({ items, className = '' }) {
  return (
    <dl className={`kv ${className}`}>
      {items.map(([k, v]) => (
        <div key={k} style={{ display: 'contents' }}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  )
}

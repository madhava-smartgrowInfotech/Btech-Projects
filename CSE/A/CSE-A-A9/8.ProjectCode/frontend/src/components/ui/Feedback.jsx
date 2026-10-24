import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { softSpring } from '../../lib/motion'
import Blobs from '../reactbits/Blobs'
import { Button } from './Button'

export function ProgressBar({ value, max = 1, tone = 'mint', label, indeterminate, height }) {
  const pct = indeterminate ? undefined : Math.max(0, Math.min(1, value / max)) * 100
  const bg = { mint: 'var(--mint)', lavender: 'var(--lavender)', peach: 'var(--peach)', sky: 'var(--sky)', rose: 'var(--rose)' }[tone]
  return (
    <div
      className={`progress ${indeterminate ? 'indeterminate' : ''}`}
      role="progressbar"
      aria-label={label}
      aria-valuemin={indeterminate ? undefined : 0}
      aria-valuemax={indeterminate ? undefined : 100}
      aria-valuenow={indeterminate ? undefined : Math.round(pct)}
      style={height ? { height } : undefined}
    >
      {indeterminate ? (
        <div className="progress-fill" />
      ) : (
        <motion.div
          className="progress-fill"
          style={{ background: bg }}
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true }}
          transition={{ type: 'spring', stiffness: 90, damping: 16 }}
        />
      )}
    </div>
  )
}

export function Skeleton({ width = '100%', height = 16, radius, className = '', style }) {
  return <div className={`skeleton ${className}`} style={{ width, height, borderRadius: radius, ...style }} aria-hidden="true" />
}

/** A page-shaped shimmer used while a screen loads. */
export function PageSkeleton({ kpis = 4, blocks = 2 }) {
  return (
    <div className="stack" role="status" aria-label="Loading">
      <div className="grid-kpi">
        {Array.from({ length: kpis }).map((_, i) => (
          <div key={i} className="card">
            <Skeleton width="55%" height={14} />
            <Skeleton width="70%" height={30} style={{ marginTop: 14 }} />
            <Skeleton width="40%" height={12} style={{ marginTop: 14 }} />
          </div>
        ))}
      </div>
      <div className="grid-2">
        {Array.from({ length: blocks }).map((_, i) => (
          <div key={i} className="card">
            <Skeleton width="40%" height={18} />
            <Skeleton height={220} radius={18} style={{ marginTop: 18 }} />
          </div>
        ))}
      </div>
      <span className="sr-only">Loading…</span>
    </div>
  )
}

export function EmptyState({ icon: Icon, title, message, action, tone = 'lavender', compact }) {
  return (
    <motion.div
      className="state"
      style={{ background: 'var(--surface-2)', padding: compact ? '32px 18px' : undefined }}
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={softSpring}
    >
      <Blobs preset="empty" />
      {Icon && (
        <motion.span
          className="state-ico"
          style={{ background: `var(--${tone})` }}
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Icon size={28} aria-hidden="true" />
        </motion.span>
      )}
      <h3 style={{ fontSize: 19 }}>{title}</h3>
      {message && <p>{message}</p>}
      {action && <div className="row" style={{ justifyContent: 'center', marginTop: 8 }}>{action}</div>}
    </motion.div>
  )
}

/** Says what failed and what to do. */
export function ErrorState({ title = 'Something went wrong', error, hint, onRetry, compact }) {
  const msg = typeof error === 'string' ? error : error?.message
  const offline = error?.status === 0 || error?.status >= 500
  return (
    <motion.div
      className="state error"
      role="alert"
      style={compact ? { padding: '28px 18px' } : undefined}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={softSpring}
    >
      <span className="state-ico" style={{ background: 'var(--rose)' }}>
        <AlertTriangle size={28} aria-hidden="true" />
      </span>
      <h3 style={{ fontSize: 19 }}>{title}</h3>
      {msg && <p>{msg}</p>}
      <p className="small">
        {hint ||
          (offline
            ? 'Start the API with run.bat (it listens on port 8309), then try again.'
            : 'Check the inputs and try again.')}
      </p>
      {onRetry && (
        <Button variant="secondary" icon={RefreshCw} onClick={() => onRetry()} style={{ marginTop: 6 }}>
          Try again
        </Button>
      )}
    </motion.div>
  )
}

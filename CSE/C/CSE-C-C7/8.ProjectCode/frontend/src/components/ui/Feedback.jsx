import { useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, Inbox, RotateCcw, X, XOctagon } from 'lucide-react'
import { Button, IconButton } from './Button'
import { useLenis } from '../motion'

/* ------------------------------------------------------------- overlays */
const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

/** Traps Tab focus inside the panel, closes on Escape, restores focus on close, pauses smooth scroll. */
const overlayStack = [] // only the top-most overlay reacts to Escape / Tab

function useOverlay(open, onCloseProp, panelRef) {
  const lenis = useLenis()
  const closeRef = useRef(onCloseProp)
  closeRef.current = onCloseProp
  useEffect(() => {
    const onClose = () => closeRef.current()
    if (!open) return undefined
    const token = {}
    overlayStack.push(token)
    const prev = document.activeElement
    lenis?.stop()
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const t = setTimeout(() => {
      const first = panelRef.current?.querySelector('[data-autofocus]') || panelRef.current?.querySelector(FOCUSABLE)
      ;(first || panelRef.current)?.focus()
    }, 30)
    const onKey = (e) => {
      if (overlayStack[overlayStack.length - 1] !== token) return
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      } else if (e.key === 'Tab' && panelRef.current) {
        const els = [...panelRef.current.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null)
        if (!els.length) return
        const first = els[0]
        const last = els[els.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      clearTimeout(t)
      overlayStack.splice(overlayStack.indexOf(token), 1)
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
      if (!overlayStack.length) lenis?.start()
      prev?.focus?.()
    }
  }, [open, panelRef, lenis])
}

export function Modal({ open, onClose, title, children, footer, describedBy }) {
  const ref = useRef(null)
  const titleId = useId()
  useOverlay(open, onClose, ref)
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
          <motion.div
            ref={ref}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={describedBy}
            tabIndex={-1}
            data-lenis-prevent
            initial={{ y: 30, rotate: -1, opacity: 0 }}
            animate={{ y: 0, rotate: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 420, damping: 30 }}
          >
            <div className="modal-head">
              <h2 id={titleId} className="display-sm">
                {title}
              </h2>
              <IconButton icon={X} label="Close dialog" size="sm" onClick={onClose} />
            </div>
            {children}
            {footer && <div className="modal-foot">{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

export function Drawer({ open, onClose, title, children, side = 'right' }) {
  const ref = useRef(null)
  const titleId = useId()
  useOverlay(open, onClose, ref)
  const from = side === 'left' ? '-100%' : '100%'
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className={`overlay drawer-overlay ${side}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.aside
            ref={ref}
            className={`drawer ${side}`}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            tabIndex={-1}
            data-lenis-prevent
            initial={{ x: from }}
            animate={{ x: 0 }}
            exit={{ x: from }}
            transition={{ type: 'spring', stiffness: 380, damping: 36 }}
          >
            <div className="modal-head">
              <h2 id={titleId} className="display-sm">
                {title}
              </h2>
              <IconButton icon={X} label="Close panel" size="sm" onClick={onClose} />
            </div>
            {children}
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

export function Tooltip({ content, children }) {
  const id = useId()
  return (
    <span className="tooltip-wrap" aria-describedby={id}>
      {children}
      <span role="tooltip" id={id} className="tooltip">
        {content}
      </span>
    </span>
  )
}

/* ---------------------------------------------------------------- states */
export function ProgressBar({ value, max = 1, label, tone }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div className="progress" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pct)}>
      <div className={`progress-bar ${tone || ''}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function Skeleton({ height = 20, width = '100%', style }) {
  return <div className="skeleton" aria-hidden="true" style={{ height, width, ...style }} />
}

export function SkeletonBlock({ rows = 3, label = 'Loading' }) {
  return (
    <div className="stack" role="status" aria-label={label} style={{ '--gap': '12px' }}>
      <span className="sr-only">{label}…</span>
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} height={i === 0 ? 34 : 18} width={i === 0 ? '45%' : `${92 - i * 12}%`} />
      ))}
    </div>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, children, action }) {
  return (
    <div className="state">
      <div className="state-icon" aria-hidden="true">
        <Icon size={30} />
      </div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  )
}

export function ErrorState({ title = 'Something went wrong', error, hint, onRetry }) {
  const msg = typeof error === 'string' ? error : error?.message
  return (
    <div className="state state-error" role="alert">
      <div className="state-icon" aria-hidden="true">
        <XOctagon size={30} />
      </div>
      <h3>{title}</h3>
      {msg && <p style={{ color: 'var(--fg)', fontWeight: 600 }}>{msg}</p>}
      <p>{hint || (error?.status === 0 ? 'The API is not reachable. Start it with run.bat, then retry.' : 'Retry, and if it keeps failing check the backend console.')}</p>
      {onRetry && (
        <Button variant="primary" icon={RotateCcw} onClick={() => onRetry()}>
          Retry
        </Button>
      )}
    </div>
  )
}

const ALERT_ICON = { error: XOctagon, success: CheckCircle2, warning: AlertTriangle, info: Info }
export function Alert({ tone = 'info', children, action }) {
  const Icon = ALERT_ICON[tone]
  return (
    <div className={`alert alert-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon size={20} aria-hidden="true" style={{ flex: 'none', marginTop: 2 }} />
      <p>{children}</p>
      {action}
    </div>
  )
}

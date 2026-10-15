import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, Inbox, RefreshCw, X, XCircle } from 'lucide-react'
import { Button, IconButton } from './controls'

const cx = (...c) => c.filter(Boolean).join(' ')

/* ------------------------------------------------------------ focus trap */
const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

function useDialog(open, onCloseProp, ref) {
  // keep the latest close handler without re-running the effect (which would steal focus)
  const closeRef = useRef(onCloseProp)
  closeRef.current = onCloseProp
  useEffect(() => {
    if (!open) return undefined
    const onClose = () => closeRef.current()
    const prev = document.activeElement
    const node = ref.current
    const first = node?.querySelector('[data-autofocus]') || node?.querySelector(FOCUSABLE)
    ;(first || node)?.focus()
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
        return
      }
      if (e.key !== 'Tab' || !node) return
      const items = [...node.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null)
      if (!items.length) {
        e.preventDefault()
        return
      }
      const a = items[0]
      const z = items[items.length - 1]
      if (e.shiftKey && document.activeElement === a) {
        e.preventDefault()
        z.focus()
      } else if (!e.shiftKey && document.activeElement === z) {
        e.preventDefault()
        a.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
      if (prev && prev.focus) prev.focus()
    }
  }, [open, ref])
}

export function Modal({ open, onClose, title, children, footer, dismissable = true }) {
  const ref = useRef(null)
  const titleId = useId()
  const close = useCallback(() => dismissable && onClose(), [dismissable, onClose])
  useDialog(open, close, ref)
  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          <motion.div className="scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.16 } }} onClick={close} />
          <div className="modal-wrap">
            <motion.div
              ref={ref}
              role="dialog"
              aria-modal="true"
              aria-labelledby={titleId}
              tabIndex={-1}
              className="modal"
              initial={{ opacity: 0, y: 24, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98, transition: { duration: 0.16 } }}
              transition={{ type: 'spring', stiffness: 380, damping: 32 }}
            >
              <div className="modal-head">
                <h2 id={titleId}>{title}</h2>
                {dismissable && <IconButton icon={X} label="Close dialog" size="sm" onClick={close} />}
              </div>
              <div className="modal-body">{children}</div>
              {footer && <div className="modal-foot">{footer}</div>}
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>,
    document.body,
  )
}

export function Drawer({ open, onClose, title, side = 'right', children, labelledBy }) {
  const ref = useRef(null)
  const titleId = useId()
  useDialog(open, onClose, ref)
  const x = side === 'right' ? '100%' : '-100%'
  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          <motion.div className="scrim" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.16 } }} onClick={onClose} />
          <motion.aside
            ref={ref}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : labelledBy}
            tabIndex={-1}
            className={cx('drawer', side)}
            initial={{ x }}
            animate={{ x: 0 }}
            exit={{ x, transition: { duration: 0.22, ease: 'easeIn' } }}
            transition={{ type: 'spring', stiffness: 360, damping: 38 }}
          >
            {title && (
              <div className="drawer-head">
                <h2 id={titleId}>{title}</h2>
                <IconButton icon={X} label="Close panel" size="sm" onClick={onClose} />
              </div>
            )}
            <div className="drawer-body">{children}</div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>,
    document.body,
  )
}

/* ------------------------------------------------------------ toasts */
const ToastCtx = createContext(() => {})
const TOAST_ICON = { success: CheckCircle2, error: XCircle, info: Info }

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const dismiss = useCallback((id) => setToasts((t) => t.filter((x) => x.id !== id)), [])
  const push = useCallback(
    ({ title, message, tone = 'success', duration = 5000 }) => {
      const id = Math.random().toString(36).slice(2)
      setToasts((t) => [...t.slice(-3), { id, title, message, tone }])
      if (duration) setTimeout(() => dismiss(id), duration)
      return id
    },
    [dismiss],
  )
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="region" aria-label="Notifications">
        <AnimatePresence initial={false}>
          {toasts.map((t) => {
            const Icon = TOAST_ICON[t.tone] || Info
            return (
              <motion.div
                key={t.id}
                layout
                className={cx('toast', `tone-${t.tone}`)}
                role={t.tone === 'error' ? 'alert' : 'status'}
                initial={{ opacity: 0, y: 16, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 40 }}
              >
                <Icon className="toast-icon" size={18} aria-hidden="true" />
                <div style={{ minWidth: 0 }}>
                  <div className="toast-title">{t.title}</div>
                  {t.message && <div className="toast-msg">{t.message}</div>}
                </div>
                <IconButton icon={X} label="Dismiss notification" size="sm" onClick={() => dismiss(t.id)} />
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)

/* ------------------------------------------------------------ tooltip */
export function Tooltip({ label, children, placement = 'top' }) {
  const [show, setShow] = useState(false)
  const id = useId()
  return (
    <span
      className="tooltip-anchor"
      onPointerEnter={() => setShow(true)}
      onPointerLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
      onKeyDown={(e) => e.key === 'Escape' && setShow(false)}
      aria-describedby={show ? id : undefined}
    >
      {children}
      <AnimatePresence>
        {show && (
          <motion.span
            id={id}
            role="tooltip"
            className={cx('tooltip', placement === 'bottom' && 'below')}
            initial={{ opacity: 0, y: placement === 'bottom' ? -4 : 4, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  )
}

/* ------------------------------------------------------------ progress + skeleton */
export function ProgressBar({ value, max = 1, label, valueLabel, indeterminate, variant }) {
  const pct = indeterminate ? undefined : Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div>
      {(label || valueLabel) && (
        <div className="progress-label">
          <span>{label}</span>
          <span>{valueLabel}</span>
        </div>
      )}
      <div
        className={cx('progress', indeterminate && 'indeterminate', variant)}
        role="progressbar"
        aria-label={label || 'Progress'}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={indeterminate ? undefined : Math.round(pct)}
      >
        <div className="progress-bar" style={indeterminate ? undefined : { width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function Skeleton({ width = '100%', height = 16, radius, style }) {
  return <span className="skeleton" aria-hidden="true" style={{ width, height, borderRadius: radius, ...style }} />
}

/* ------------------------------------------------------------ states */
export function EmptyState({ icon: Icon = Inbox, title, children, actions }) {
  return (
    <div className="state">
      <span className="state-icon">
        <Icon size={24} aria-hidden="true" />
      </span>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {actions && <div className="row">{actions}</div>}
    </div>
  )
}

export function ErrorState({ title = 'Something went wrong', error, onRetry, children }) {
  return (
    <div className="state error" role="alert">
      <span className="state-icon">
        <AlertTriangle size={24} aria-hidden="true" />
      </span>
      <h3>{title}</h3>
      <p>{error?.message || String(error || '')}</p>
      {children}
      {onRetry && (
        <div className="row">
          <Button icon={RefreshCw} onClick={() => onRetry()}>
            Try again
          </Button>
        </div>
      )}
    </div>
  )
}

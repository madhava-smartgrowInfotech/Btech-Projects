import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, RefreshCw, X, XCircle } from 'lucide-react'
import { cloneElement, createContext, isValidElement, useCallback, useContext, useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useReducedMotion } from '../../lib/reduced'

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

// Traps Tab inside `ref` while open, closes on Escape and gives focus back on close.
export function useFocusTrap(ref, open, onClose) {
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    if (!open) return
    const prev = document.activeElement
    const el = ref.current
    const t = setTimeout(() => {
      const first = el?.querySelector('[data-autofocus]') || el?.querySelector(FOCUSABLE)
      ;(first || el)?.focus()
    }, 20)
    function key(e) {
      if (e.key === 'Escape') {
        e.stopPropagation()
        close.current?.()
        return
      }
      if (e.key !== 'Tab' || !el) return
      const items = [...el.querySelectorAll(FOCUSABLE)].filter((n) => n.offsetParent !== null)
      if (!items.length) return
      const first = items[0], last = items[items.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', key, true)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      clearTimeout(t)
      document.removeEventListener('keydown', key, true)
      document.body.style.overflow = overflow
      prev?.focus?.()
    }
  }, [open, ref])
}

export function Modal({ open, onClose, title, children, footer, size = 'md' }) {
  const ref = useRef(null)
  const id = useId()
  const reduced = useReducedMotion()
  useFocusTrap(ref, open, onClose)
  const w = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-2xl' }[size]
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[12vh]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-[var(--overlay)] backdrop-blur-[2px]" onClick={onClose} aria-hidden="true" />
          <motion.div ref={ref} role="dialog" aria-modal="true" aria-labelledby={title ? id : undefined} tabIndex={-1}
            className={`panel scan relative w-full ${w} overflow-hidden outline-none`}
            initial={{ opacity: 0, y: reduced ? 0 : 12, scale: reduced ? 1 : 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: reduced ? 0 : 8 }} transition={{ duration: 0.2 }}>
            {title && (
              <div className="flex items-center justify-between border-b border-line px-4 py-3">
                <h2 id={id} className="font-mono text-xs uppercase tracking-[0.14em] text-muted">{title}</h2>
                <button type="button" onClick={onClose} aria-label="Close" className="rounded p-1 text-dim hover:text-fg"><X size={16} /></button>
              </div>
            )}
            <div className="relative z-[1]">{children}</div>
            {footer && <div className="relative z-[1] flex justify-end gap-2 border-t border-line px-4 py-3">{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

export function Drawer({ open, onClose, title, side = 'right', children, width = 'w-[min(420px,92vw)]' }) {
  const ref = useRef(null)
  const id = useId()
  const reduced = useReducedMotion()
  useFocusTrap(ref, open, onClose)
  const off = reduced ? 0 : side === 'right' ? '100%' : '-100%'
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[55]" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-[var(--overlay)]" onClick={onClose} aria-hidden="true" />
          <motion.aside ref={ref} role="dialog" aria-modal="true" aria-labelledby={id} tabIndex={-1}
            className={`absolute top-0 ${side === 'right' ? 'right-0 border-l' : 'left-0 border-r'} flex h-full ${width} flex-col border-line bg-panel outline-none`}
            initial={{ x: off, opacity: reduced ? 0 : 1 }} animate={{ x: 0, opacity: 1 }} exit={{ x: off, opacity: reduced ? 0 : 1 }}
            transition={{ type: 'tween', duration: 0.25, ease: [0.2, 0.8, 0.2, 1] }}>
            <div className="flex items-center justify-between border-b border-line px-4 py-3">
              <h2 id={id} className="font-mono text-xs uppercase tracking-[0.14em] text-muted">{title}</h2>
              <button type="button" onClick={onClose} aria-label="Close" className="rounded p-1 text-dim hover:text-fg"><X size={16} /></button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

// ---------- toasts ----------
const ToastContext = createContext(() => {})
export const useToast = () => useContext(ToastContext)
const TOAST_ICON = { ok: CheckCircle2, alert: XCircle, warn: AlertTriangle, info: Info }

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const reduced = useReducedMotion()
  const dismiss = useCallback((id) => setItems((xs) => xs.filter((x) => x.id !== id)), [])
  const toast = useCallback((t) => {
    const id = Math.random().toString(36).slice(2)
    setItems((xs) => [...xs.slice(-3), { id, tone: 'ok', ...t }])
    setTimeout(() => dismiss(id), t.duration || 4500)
  }, [dismiss])
  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[70] flex w-[min(360px,calc(100vw-2rem))] flex-col gap-2" role="status" aria-live="polite">
        <AnimatePresence initial={false}>
          {items.map((t) => {
            const Icon = TOAST_ICON[t.tone] || Info
            return (
              <motion.div key={t.id} layout={!reduced} initial={{ opacity: 0, x: reduced ? 0 : 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: reduced ? 0 : 24 }}
                className="panel pointer-events-auto flex items-start gap-3 p-3">
                <Icon size={17} className="mt-0.5 shrink-0" style={{ color: `var(--${t.tone})` }} aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-fg">{t.title}</div>
                  {t.body && <div className="mt-0.5 text-xs text-muted">{t.body}</div>}
                </div>
                <button type="button" onClick={() => dismiss(t.id)} aria-label="Dismiss" className="rounded p-0.5 text-dim hover:text-fg"><X size={14} /></button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}

// Hover/focus tooltip (display:none otherwise, so it never widens the page). `decorative` when the trigger
// already has the same accessible name; `align="end"` for triggers at the right edge.
export function Tooltip({ content, children, side = 'bottom', align = 'center', decorative = true }) {
  const id = useId()
  const pos = side === 'top' ? 'bottom-full mb-1.5' : 'top-full mt-1.5'
  const child = !decorative && isValidElement(children) ? cloneElement(children, { 'aria-describedby': id }) : children
  return (
    <span className="group/tt relative inline-flex">
      {child}
      <span id={id} role={decorative ? undefined : 'tooltip'} aria-hidden={decorative || undefined}
        className={`pointer-events-none absolute ${align === 'end' ? 'right-0' : 'left-1/2 -translate-x-1/2'} ${pos} z-50 hidden whitespace-nowrap rounded border border-line-strong bg-panel px-2 py-1 font-mono text-[11px] text-fg shadow-lg group-hover/tt:block group-focus-within/tt:block`}>
        {content}
      </span>
    </span>
  )
}

export function ProgressBar({ value = 0, label, tone = 'ok', segments = 40 }) {
  const lit = Math.round((Math.max(0, Math.min(100, value)) / 100) * segments)
  return (
    <div>
      {label && (
        <div className="mb-1.5 flex justify-between font-mono text-[11px] text-muted">
          <span className="truncate">{label}</span><span className="tabular-nums text-fg">{Math.round(value)}%</span>
        </div>
      )}
      <div role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value)} aria-label={label || 'Progress'}
        className="flex h-2.5 gap-[2px]">
        {Array.from({ length: segments }, (_, i) => (
          <span key={i} className="flex-1 rounded-[1px] transition-colors duration-300"
            style={{ background: i < lit ? `var(--${tone})` : 'var(--line-strong)', opacity: i < lit ? 1 : 0.5 }} />
        ))}
      </div>
    </div>
  )
}

export function Skeleton({ className = 'h-4 w-full' }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />
}

export function PageSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true" aria-label="Loading">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}</div>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3"><Skeleton className="h-72 lg:col-span-2" /><Skeleton className="h-72" /></div>
    </div>
  )
}

export function EmptyState({ icon: Icon = Info, title, body, action, className = '' }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-2 px-4 py-10 text-center ${className}`}>
      <div className="grid h-11 w-11 place-items-center rounded-[6px] border border-line-strong text-dim"><Icon size={19} aria-hidden="true" /></div>
      <div className="mt-1 font-mono text-sm text-fg">{title}</div>
      {body && <p className="max-w-sm text-xs text-muted">{body}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

// error: { message, hint } from describeError, or a plain string
export function ErrorState({ error, onRetry, title = 'Request failed', compact = false }) {
  if (!error) return null
  const msg = typeof error === 'string' ? error : error.message
  const hint = typeof error === 'string' ? null : error.hint
  return (
    <div role="alert" className={`flex items-start gap-3 rounded-[6px] border border-alert/35 bg-alert/[0.07] ${compact ? 'p-2.5' : 'p-4'}`}>
      <AlertTriangle size={17} className="mt-0.5 shrink-0 text-alert" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-alert">{title}</div>
        <div className="mt-0.5 break-words text-sm text-fg">{msg}</div>
        {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
      </div>
      {onRetry && (
        <button type="button" onClick={onRetry} className="inline-flex shrink-0 items-center gap-1.5 rounded border border-alert/40 px-2 py-1 font-mono text-[11px] uppercase text-alert hover:bg-alert/10">
          <RefreshCw size={12} /> Retry
        </button>
      )}
    </div>
  )
}

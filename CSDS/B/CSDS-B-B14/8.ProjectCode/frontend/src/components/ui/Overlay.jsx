import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { softSpring, spring } from '../../lib/motion'
import { IconButton } from './Button'

const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

/** Escape closes, Tab is trapped inside, focus returns to the opener. */
function useDialog(open, onCloseProp, ref) {
  const close = useRef(onCloseProp)
  close.current = onCloseProp
  useEffect(() => {
    const onClose = () => close.current?.()
    if (!open) return undefined
    const prev = document.activeElement
    const body = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const t = setTimeout(() => {
      const el = ref.current
      const first = el?.querySelector('[data-autofocus]') || el?.querySelector(FOCUSABLE)
      ;(first || el)?.focus()
    }, 30)
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
      if (e.key === 'Tab' && ref.current) {
        const items = [...ref.current.querySelectorAll(FOCUSABLE)].filter((n) => n.offsetParent !== null)
        if (!items.length) return
        const first = items[0]
        const last = items[items.length - 1]
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
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = body
      prev?.focus?.()
    }
  }, [open, ref])
}

export function Modal({ open, onClose, title, description, children, footer }) {
  const ref = useRef(null)
  const tid = useId()
  const did = useId()
  useDialog(open, onClose, ref)
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
          <motion.div
            ref={ref}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby={tid}
            aria-describedby={description ? did : undefined}
            tabIndex={-1}
            initial={{ opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 10 }}
            transition={spring}
          >
            <div className="modal-head">
              <div>
                <h2 id={tid}>{title}</h2>
                {description && (
                  <p id={did} className="muted small" style={{ marginTop: 6 }}>
                    {description}
                  </p>
                )}
              </div>
              <IconButton icon={X} label="Close dialog" plain onClick={onClose} />
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

export function Drawer({ open, onClose, title, side = 'left', children }) {
  const ref = useRef(null)
  const tid = useId()
  useDialog(open, onClose, ref)
  const off = side === 'left' ? '-100%' : '100%'
  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div className="overlay drawer-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
          <motion.aside
            ref={ref}
            className={`drawer ${side}`}
            role="dialog"
            aria-modal="true"
            aria-labelledby={tid}
            tabIndex={-1}
            initial={{ x: off }}
            animate={{ x: 0 }}
            exit={{ x: off }}
            transition={softSpring}
          >
            <div className="row between">
              <h2 id={tid} style={{ fontSize: 17 }}>
                {title}
              </h2>
              <IconButton icon={X} label="Close" plain onClick={onClose} />
            </div>
            {children}
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}

/** Shows on hover and keyboard focus. */
export function Tooltip({ content, children }) {
  const [show, setShow] = useState(false)
  const id = useId()
  return (
    <span
      className="tooltip-wrap"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
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
            className="tooltip"
            initial={{ opacity: 0, y: 6, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            transition={spring}
          >
            {content}
          </motion.span>
        )}
      </AnimatePresence>
    </span>
  )
}

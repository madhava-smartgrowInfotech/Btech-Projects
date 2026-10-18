import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react'
import { spring } from '../../lib/motion'

const ToastCtx = createContext(() => {})
const KIND = {
  success: { icon: CheckCircle2, bg: 'var(--mint)' },
  error: { icon: AlertTriangle, bg: 'var(--rose)' },
  info: { icon: Info, bg: 'var(--sky)' },
}

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const n = useRef(0)
  const dismiss = useCallback((id) => setItems((xs) => xs.filter((x) => x.id !== id)), [])
  const toast = useCallback(
    ({ kind = 'info', title, message, duration = 5000 }) => {
      const id = ++n.current
      setItems((xs) => [...xs.slice(-3), { id, kind, title, message }])
      if (duration) setTimeout(() => dismiss(id), duration)
    },
    [dismiss],
  )
  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="toasts" aria-live="polite" aria-atomic="false">
        <AnimatePresence initial={false}>
          {items.map((t) => {
            const k = KIND[t.kind] || KIND.info
            const Icon = k.icon
            return (
              <motion.div
                key={t.id}
                layout
                className="toast"
                role={t.kind === 'error' ? 'alert' : 'status'}
                initial={{ opacity: 0, y: -16, scale: 0.92 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 40, scale: 0.95 }}
                transition={spring}
              >
                <span className="toast-ico" style={{ background: k.bg }}>
                  <Icon size={18} aria-hidden="true" />
                </span>
                <div className="toast-body">
                  <strong>{t.title}</strong>
                  {t.message && <span>{t.message}</span>}
                </div>
                <button type="button" className="icon-btn plain" style={{ width: 34, height: 34 }} aria-label="Dismiss notification" onClick={() => dismiss(t.id)}>
                  <X size={16} aria-hidden="true" />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)

import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Info, X, XOctagon } from 'lucide-react'

const ToastCtx = createContext(null)
const ICONS = { success: CheckCircle2, error: XOctagon, warning: AlertTriangle, info: Info }

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])
  const seq = useRef(0)

  const dismiss = useCallback((id) => setItems((xs) => xs.filter((t) => t.id !== id)), [])
  const push = useCallback(
    (kind, message, ms = kind === 'error' ? 7000 : 4500) => {
      const id = ++seq.current
      setItems((xs) => [...xs.slice(-3), { id, kind, message }])
      if (ms) setTimeout(() => dismiss(id), ms)
      return id
    },
    [dismiss],
  )

  const api = useMemo(
    () => ({
      success: (m, ms) => push('success', m, ms),
      error: (m, ms) => push('error', m, ms),
      warning: (m, ms) => push('warning', m, ms),
      info: (m, ms) => push('info', m, ms),
      dismiss,
    }),
    [push, dismiss],
  )

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="toasts" role="region" aria-label="Notifications" aria-live="polite">
        <AnimatePresence initial={false}>
          {items.map((t) => {
            const Icon = ICONS[t.kind]
            return (
              <motion.div
                key={t.id}
                className={`toast toast-${t.kind}`}
                role={t.kind === 'error' ? 'alert' : 'status'}
                initial={{ x: 40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 40, opacity: 0 }}
                transition={{ type: 'spring', stiffness: 500, damping: 34 }}
              >
                <Icon size={20} aria-hidden="true" />
                <p>{t.message}</p>
                <button className="icon-btn sm" onClick={() => dismiss(t.id)} aria-label="Dismiss notification">
                  <X size={16} />
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

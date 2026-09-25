import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, CheckCircle2, Info } from 'lucide-react'

import { useToastStore } from '@/store/toast'

const ICONS = {
  default: Info,
  success: CheckCircle2,
  error: AlertCircle,
}

const RING = {
  default: 'border-white/10',
  success: 'border-emerald-500/30',
  error: 'border-red-500/30',
}

export function Toaster() {
  const toasts = useToastStore((s) => s.toasts)

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-[100] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((t) => {
          const Icon = ICONS[t.variant ?? 'default']
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.9 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              className={`glass-panel pointer-events-auto flex w-80 items-start gap-3 rounded-xl border ${RING[t.variant ?? 'default']} p-3.5 shadow-2xl`}
            >
              <Icon
                size={18}
                className={
                  t.variant === 'success'
                    ? 'text-emerald-400'
                    : t.variant === 'error'
                      ? 'text-red-400'
                      : 'text-brand-400'
                }
              />
              <div>
                <p className="text-sm font-medium text-white">{t.title}</p>
                {t.description && <p className="mt-0.5 text-xs text-ink-400">{t.description}</p>}
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

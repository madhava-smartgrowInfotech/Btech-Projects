import * as React from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { AnimatePresence, motion } from 'framer-motion'
import { create } from 'zustand'
import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react'
import { cn, EASE_EXPO } from '@/lib/utils'

type ToastTone = 'default' | 'success' | 'warning' | 'error'

export type ToastItem = {
  id: string
  title: string
  description?: string
  tone?: ToastTone
}

type ToastState = {
  items: ToastItem[]
  push: (t: Omit<ToastItem, 'id'>) => void
  dismiss: (id: string) => void
}

const useToastStore = create<ToastState>((set) => ({
  items: [],
  push: (t) =>
    set((s) => ({
      items: [...s.items, { ...t, id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}` }].slice(
        -4,
      ),
    })),
  dismiss: (id) => set((s) => ({ items: s.items.filter((i) => i.id !== id) })),
}))

export function toast(t: Omit<ToastItem, 'id'>) {
  useToastStore.getState().push(t)
}

const toneIcon: Record<ToastTone, React.ReactNode> = {
  default: <Info className="h-4 w-4 text-cobalt-300" />,
  success: <CheckCircle2 className="h-4 w-4 text-teal-400" />,
  warning: <TriangleAlert className="h-4 w-4 text-amber-300" />,
  error: <TriangleAlert className="h-4 w-4 text-rose-400" />,
}

export function Toaster() {
  const items = useToastStore((s) => s.items)
  const dismiss = useToastStore((s) => s.dismiss)

  return (
    <ToastPrimitive.Provider swipeDirection="right" duration={4200}>
      <AnimatePresence initial={false}>
        {items.map((item) => (
          <ToastPrimitive.Root
            key={item.id}
            open
            onOpenChange={(open) => !open && dismiss(item.id)}
            asChild
            forceMount
          >
            <motion.li
              layout
              initial={{ opacity: 0, y: 14, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.97 }}
              transition={{ duration: 0.42, ease: EASE_EXPO }}
              className={cn(
                'pointer-events-auto flex w-[min(92vw,380px)] items-start gap-3 rounded-xl border border-white/[0.08] bg-ink-875/95 p-4 shadow-lift backdrop-blur-xl',
              )}
            >
              <span className="mt-0.5 shrink-0">{toneIcon[item.tone ?? 'default']}</span>
              <div className="min-w-0 flex-1">
                <ToastPrimitive.Title className="text-[13px] font-medium tracking-tight text-ink-100">
                  {item.title}
                </ToastPrimitive.Title>
                {item.description && (
                  <ToastPrimitive.Description className="mt-1 text-[12px] leading-relaxed text-ink-400">
                    {item.description}
                  </ToastPrimitive.Description>
                )}
              </div>
              <ToastPrimitive.Close className="shrink-0 rounded-full p-1 text-ink-500 transition-colors hover:bg-white/[0.07] hover:text-ink-200">
                <X className="h-3.5 w-3.5" />
              </ToastPrimitive.Close>
            </motion.li>
          </ToastPrimitive.Root>
        ))}
      </AnimatePresence>
      <ToastPrimitive.Viewport className="pointer-events-none fixed bottom-5 right-5 z-[90] flex max-h-screen w-auto list-none flex-col gap-2.5 outline-none" />
    </ToastPrimitive.Provider>
  )
}

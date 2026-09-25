import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Activity, Clock } from 'lucide-react'

import { getQueueBoard } from '@/lib/api'
import { useLiveSocket } from '@/hooks/useLiveSocket'
import type { QueueBoardEntry } from '@/types'

export default function WaitingBoard() {
  const [board, setBoard] = useState<QueueBoardEntry[]>([])
  const [now, setNow] = useState(new Date())

  async function refresh() {
    try {
      setBoard(await getQueueBoard())
    } catch {
      /* board stays on last known state if a refresh fails */
    }
  }

  useEffect(() => {
    refresh()
    const poll = setInterval(refresh, 15000)
    const clock = setInterval(() => setNow(new Date()), 1000)
    return () => {
      clearInterval(poll)
      clearInterval(clock)
    }
  }, [])

  useLiveSocket((evt) => {
    if (['visit_created', 'visit_updated'].includes(evt.event)) refresh()
  })

  return (
    <div className="min-h-screen bg-ink-950 bg-grid px-8 py-8 text-white">
      <div className="pointer-events-none fixed inset-x-0 top-0 h-96 bg-gradient-to-b from-brand-500/10 to-transparent" />

      <header className="relative z-10 mb-10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-400 to-vital-500 shadow-lg shadow-brand-500/30">
            <Activity size={22} className="text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="font-display text-xl font-bold">
              Med<span className="text-brand-400">Flow</span>
            </p>
            <p className="text-xs text-ink-400">Waiting Room Board</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-lg font-medium text-ink-200">
          <Clock size={18} className="text-brand-400" />
          {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </div>
      </header>

      <div className="relative z-10 grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {board.map((dept) => (
          <motion.div
            key={dept.code}
            layout
            className="rounded-3xl border border-white/8 bg-ink-850/70 p-6"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-semibold text-ink-100">{dept.department}</h2>
              <span className="rounded-full bg-white/5 px-2.5 py-1 text-[11px] font-medium text-ink-400">
                {dept.code}
              </span>
            </div>

            <div className="mt-6 text-center">
              <p className="text-[11px] font-semibold uppercase tracking-widest text-ink-500">
                Now Serving
              </p>
              <AnimatePresence mode="wait">
                <motion.p
                  key={dept.now_serving}
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ type: 'spring', stiffness: 300, damping: 22 }}
                  className="font-display text-5xl font-extrabold tracking-tight text-brand-300"
                >
                  {dept.now_serving}
                </motion.p>
              </AnimatePresence>
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-white/8 pt-4 text-sm">
              <div>
                <p className="text-ink-500">Waiting</p>
                <p className="font-semibold text-white">{dept.waiting_count}</p>
              </div>
              <div className="text-right">
                <p className="text-ink-500">Est. wait</p>
                <p className="font-semibold text-white">{Math.round(dept.avg_wait_minutes)} min</p>
              </div>
            </div>

            {dept.upcoming.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {dept.upcoming.map((token) => (
                  <span
                    key={token}
                    className="rounded-lg bg-ink-900/80 px-2.5 py-1 font-mono text-xs text-ink-400"
                  >
                    {token}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}

import { AnimatePresence, motion } from 'framer-motion'
import { Eraser, TerminalSquare } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { clock } from '../../format'
import { clearActivity, useActivity } from '../../lib/activity'
import { useReducedMotion } from '../../lib/reduced'
import { IconButton, Switch } from './controls'
import { StatusDot } from './display'
import Typewriter from './Typewriter'

const KIND = {
  api: ['API', 'var(--ok)'], pipeline: ['RUN', 'var(--warn)'], auth: ['AUTH', 'var(--info)'], error: ['ERR', 'var(--alert)'],
  history: ['HIST', 'var(--cyan)'], ui: ['UI', 'var(--muted)'], health: ['SYS', 'var(--cyan)'],
}

// Terminal-style log that streams the real events recorded in lib/activity (API calls, pipeline stages, auth).
export default function ActivityLog({ height = 300, framed = true, title = 'activity.log' }) {
  const events = useActivity()
  const [follow, setFollow] = useState(true)
  const box = useRef(null)
  const reduced = useReducedMotion()
  const newest = events[events.length - 1]?.id

  useEffect(() => {
    if (follow && box.current) box.current.scrollTop = box.current.scrollHeight
  }, [events, follow])

  return (
    <div className={`${framed ? 'panel scan' : ''} flex min-w-0 flex-col overflow-hidden`}>
      <div className="relative z-[1] flex items-center justify-between gap-2 border-b border-line px-3 py-2">
        <div className="flex min-w-0 items-center gap-2 font-mono text-[11px] text-muted">
          <TerminalSquare size={14} className="text-ok" aria-hidden="true" />
          <span className="truncate">~/taxsentinel/{title}</span>
          <StatusDot tone="ok" />
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={follow} onChange={setFollow} label="follow" />
          <IconButton size="sm" icon={Eraser} label="Clear log" onClick={clearActivity} />
        </div>
      </div>
      <div ref={box} role="log" aria-live="polite" aria-label="Activity log" tabIndex={0}
        className="relative z-[1] overflow-y-auto bg-bg/40 px-3 py-2 font-mono text-[11.5px] leading-[1.7]" style={{ height }}>
        {events.length === 0 && <div className="text-dim">waiting for events…</div>}
        <AnimatePresence initial={false}>
          {events.map((e) => {
            const [tag, color] = KIND[e.kind] || KIND.ui
            return (
              <motion.div key={e.id} initial={{ opacity: 0, x: reduced ? 0 : -6 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}
                className="flex gap-2 whitespace-nowrap">
                <span className="text-dim">{clock(e.t)}</span>
                <span className="w-9 shrink-0" style={{ color }}>{tag}</span>
                <span className="min-w-0 truncate text-fg/90" title={e.text}>
                  {e.id === newest && !reduced ? <Typewriter text={e.text} speed={7} caret={false} /> : e.text}
                </span>
              </motion.div>
            )
          })}
        </AnimatePresence>
        <div className="flex gap-2 text-ok"><span>$</span><span className="tw-caret" aria-hidden="true" /></div>
      </div>
    </div>
  )
}

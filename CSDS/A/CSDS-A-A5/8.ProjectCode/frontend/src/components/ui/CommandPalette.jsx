import { CornerDownLeft, User } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { errorMessage } from '../../api'
import { riskVar } from '../../format'
import { SearchField } from './controls'
import { Modal } from './feedback'

// `/` opens this: jump to a screen or find a taxpayer by name / GSTIN (live /api/taxpayers search).
export default function CommandPalette({ open, onClose, nav }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState([])
  const [state, setState] = useState('idle')
  const [active, setActive] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) { setQ(''); setHits([]); setActive(0); setState('idle') }
  }, [open])

  useEffect(() => {
    const term = q.trim()
    if (term.length < 2) { setHits([]); setState('idle'); return }
    setState('loading')
    const t = setTimeout(() => {
      api.get('/taxpayers', { params: { q: term, limit: 7 } })
        .then((r) => { setHits(r.data.items); setState(r.data.items.length ? 'done' : 'empty') })
        .catch((e) => { setHits([]); setState(errorMessage(e)) })
    }, 220)
    return () => clearTimeout(t)
  }, [q])

  const options = useMemo(() => {
    const term = q.trim().toLowerCase()
    const screens = nav.filter((n) => !term || n.label.toLowerCase().includes(term))
      .map((n) => ({ id: `nav-${n.to}`, to: n.to, label: n.label, kind: 'screen', icon: n.icon, hint: `g ${n.key}` }))
    const people = hits.map((t) => ({ id: `tp-${t.gstin}`, to: `/app/taxpayers/${t.gstin}`, label: t.legal_name, kind: 'taxpayer', sub: t.gstin, risk: t.risk }))
    return [...screens, ...people]
  }, [q, hits, nav])

  useEffect(() => { setActive(0) }, [options.length])

  function go(o) {
    if (!o) return
    onClose()
    navigate(o.to)
  }
  function key(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(options.length - 1, a + 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(0, a - 1)) }
    else if (e.key === 'Enter') { e.preventDefault(); go(options[active]) }
  }

  return (
    <Modal open={open} onClose={onClose} title="Command / search">
      <div className="p-3">
        <SearchField value={q} onChange={setQ} placeholder="Search taxpayers or jump to a screen…" label="Search taxpayers or screens"
          onKeyDown={key} data-autofocus role="combobox" aria-expanded="true" aria-controls="palette-list"
          aria-activedescendant={options[active]?.id} autoComplete="off" />
      </div>
      <ul id="palette-list" role="listbox" aria-label="Results" className="max-h-[50vh] overflow-y-auto border-t border-line p-1.5">
        {options.map((o, i) => {
          const Icon = o.icon || User
          return (
            <li key={o.id} id={o.id} role="option" aria-selected={i === active}
              onMouseEnter={() => setActive(i)} onClick={() => go(o)}
              className={`flex cursor-pointer items-center gap-3 rounded-[4px] px-2.5 py-2 text-sm ${i === active ? 'bg-ok/10 text-fg' : 'text-muted'}`}>
              <Icon size={15} className={i === active ? 'text-ok' : 'text-dim'} aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate">
                {o.label}
                {o.sub && <span className="ml-2 font-mono text-[11px] text-dim">{o.sub}</span>}
              </span>
              {o.risk !== undefined && <span className="font-mono text-xs" style={{ color: riskVar(o.risk) }}>{o.risk.toFixed(2)}</span>}
              {o.hint && <kbd className="rounded border border-line-strong px-1.5 font-mono text-[10px] text-dim">{o.hint}</kbd>}
              {i === active && <CornerDownLeft size={13} className="text-ok" aria-hidden="true" />}
            </li>
          )
        })}
        {state === 'loading' && <li className="px-2.5 py-2 font-mono text-xs text-dim">searching…</li>}
        {state === 'empty' && <li className="px-2.5 py-2 font-mono text-xs text-dim">no taxpayer matches “{q}”</li>}
        {!['idle', 'loading', 'empty', 'done'].includes(state) && <li className="px-2.5 py-2 text-xs text-alert">{state}</li>}
      </ul>
      <div className="flex flex-wrap gap-3 border-t border-line px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-dim">
        <span>↑↓ move</span><span>↵ open</span><span>esc close</span>
      </div>
    </Modal>
  )
}

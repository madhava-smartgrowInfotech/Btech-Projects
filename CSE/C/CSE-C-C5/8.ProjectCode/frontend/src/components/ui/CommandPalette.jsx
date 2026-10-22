import { Building2, CornerDownLeft } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { lpa } from '../../format'
import { useData } from '../../lib/data'
import { SearchField } from './controls'
import { Modal } from './feedback'

// `/` opens this: jump to a screen or find a company by name / location (searches the loaded company list).
export default function CommandPalette({ open, onClose, nav }) {
  const [q, setQ] = useState('')
  const [active, setActive] = useState(0)
  const navigate = useNavigate()
  const { companies } = useData()

  useEffect(() => {
    if (!open) { setQ(''); setActive(0) }
  }, [open])

  const options = useMemo(() => {
    const term = q.trim().toLowerCase()
    const screens = nav.filter((n) => !term || n.label.toLowerCase().includes(term))
      .map((n) => ({ id: `nav-${n.to}`, to: n.to, label: n.label, icon: n.icon, hint: `g ${n.key}` }))
    const hits = term.length < 2 || !companies ? [] : companies
      .filter((c) => `${c.Company} ${c.Location} ${c.Company_Type}`.toLowerCase().includes(term)).slice(0, 7)
      .map((c) => ({ id: `co-${c.Company.replace(/\W/g, '_')}`, to: `/companies?q=${encodeURIComponent(c.Company)}`, label: c.Company, sub: `${c.Location} · tier ${c.Tier}`, price: lpa(c.Package_LPA) }))
    return [...screens, ...hits]
  }, [q, companies, nav])

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
        <SearchField value={q} onChange={setQ} placeholder="Search companies or jump to a screen…" label="Search companies or screens"
          onKeyDown={key} data-autofocus role="combobox" aria-expanded="true" aria-controls="palette-list"
          aria-activedescendant={options[active]?.id} autoComplete="off" />
      </div>
      <ul id="palette-list" role="listbox" aria-label="Results" className="max-h-[50vh] overflow-y-auto border-t border-line p-1.5">
        {options.map((o, i) => {
          const Icon = o.icon || Building2
          return (
            <li key={o.id} id={o.id} role="option" aria-selected={i === active}
              onMouseEnter={() => setActive(i)} onClick={() => go(o)}
              className={`flex cursor-pointer items-center gap-3 rounded-[4px] px-2.5 py-2 text-sm ${i === active ? 'bg-ok/10 text-fg' : 'text-muted'}`}>
              <Icon size={15} className={i === active ? 'text-ok' : 'text-dim'} aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate">
                {o.label}
                {o.sub && <span className="ml-2 font-mono text-[11px] text-dim">{o.sub}</span>}
              </span>
              {o.price && <span className="font-mono text-xs text-ok">{o.price}</span>}
              {o.hint && <kbd className="rounded border border-line-strong px-1.5 font-mono text-[10px] text-dim">{o.hint}</kbd>}
              {i === active && <CornerDownLeft size={13} className="text-ok" aria-hidden="true" />}
            </li>
          )
        })}
        {q.trim().length >= 2 && options.every((o) => o.id.startsWith('nav-')) && <li className="px-2.5 py-2 font-mono text-xs text-dim">no company matches “{q}”</li>}
      </ul>
      <div className="flex flex-wrap gap-3 border-t border-line px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-dim">
        <span>↑↓ move</span><span>↵ open</span><span>esc close</span>
      </div>
    </Modal>
  )
}

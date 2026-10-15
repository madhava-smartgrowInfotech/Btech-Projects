import { CornerDownLeft, Hand } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { errorMessage } from '../../api'
import { label as pretty } from '../../format'
import { SearchField } from './controls'
import { Modal } from './feedback'

// `/` opens this: jump to a screen or find a sign in the vocabulary (live /api/vocab) and practise it.
export default function CommandPalette({ open, onClose, nav }) {
  const [q, setQ] = useState('')
  const [vocab, setVocab] = useState(null)
  const [error, setError] = useState('')
  const [active, setActive] = useState(0)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) { setQ(''); setActive(0); return }
    if (vocab) return
    api.get('/vocab', { silent: true }).then((r) => { setVocab(r.data); setError('') }).catch((e) => setError(errorMessage(e)))
  }, [open, vocab])

  const options = useMemo(() => {
    const term = q.trim().toLowerCase()
    const screens = nav.filter((n) => !term || n.label.toLowerCase().includes(term))
      .map((n) => ({ id: `nav-${n.to}`, to: n.to, label: n.label, icon: n.icon, hint: `g ${n.key}` }))
    if (term.length < 1 || !vocab) return screens
    const words = vocab.words
      .filter((w) => w.gloss.toLowerCase().includes(term.replaceAll(' ', '_')) || w.text.includes(term))
      .slice(0, 6)
      .map((w) => ({ id: `w-${w.gloss}`, to: `/app/practice?target=${encodeURIComponent(w.gloss)}`, label: `Practise “${pretty(w.gloss)}”`, sub: w.category, icon: Hand }))
    const letters = vocab.letters
      .filter((l) => l.toLowerCase() === term)
      .map((l) => ({ id: `l-${l}`, to: `/app/practice?target=${encodeURIComponent(l)}`, label: `Practise letter “${l}”`, sub: 'fingerspelling', icon: Hand }))
    return [...screens, ...words, ...letters]
  }, [q, vocab, nav])

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
        <SearchField value={q} onChange={setQ} placeholder="Jump to a screen or find a sign…" label="Search screens and signs"
          onKeyDown={key} data-autofocus role="combobox" aria-expanded="true" aria-controls="palette-list"
          aria-activedescendant={options[active]?.id} autoComplete="off" />
      </div>
      <ul id="palette-list" role="listbox" aria-label="Results" className="max-h-[50vh] overflow-y-auto border-t border-line p-1.5">
        {options.map((o, i) => {
          const Icon = o.icon
          return (
            <li key={o.id} id={o.id} role="option" aria-selected={i === active}
              onMouseEnter={() => setActive(i)} onClick={() => go(o)}
              className={`flex cursor-pointer items-center gap-3 rounded-[4px] px-2.5 py-2 text-sm ${i === active ? 'bg-ok/10 text-fg' : 'text-muted'}`}>
              <Icon size={15} className={i === active ? 'text-ok' : 'text-dim'} aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate">
                {o.label}
                {o.sub && <span className="ml-2 font-mono text-[11px] text-dim">{o.sub}</span>}
              </span>
              {o.hint && <kbd className="rounded border border-line-strong px-1.5 font-mono text-[10px] text-dim">{o.hint}</kbd>}
              {i === active && <CornerDownLeft size={13} className="text-ok" aria-hidden="true" />}
            </li>
          )
        })}
        {options.length === 0 && <li className="px-2.5 py-2 font-mono text-xs text-dim">nothing matches “{q}”</li>}
        {error && <li className="px-2.5 py-2 text-xs text-alert">Sign search unavailable: {error}</li>}
      </ul>
      <div className="flex flex-wrap gap-3 border-t border-line px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-dim">
        <span>↑↓ move</span><span>↵ open</span><span>esc close</span>
      </div>
    </Modal>
  )
}

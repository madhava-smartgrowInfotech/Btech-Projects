// Minimal renderer for the case-note Markdown Gemini returns (## headings, bullets, **bold**, [E#] citations).
function inline(text, onCite, keyBase) {
  const parts = text.split(/(\*\*[^*]+\*\*|\[E\d+\])/g)
  return parts.map((p, i) => {
    const k = `${keyBase}-${i}`
    if (/^\*\*[^*]+\*\*$/.test(p)) return <strong key={k}>{p.slice(2, -2)}</strong>
    const m = p.match(/^\[(E\d+)\]$/)
    if (m)
      return (
        <button key={k} type="button" onClick={() => onCite?.(m[1])}
          className="mx-0.5 rounded bg-indigo-50 px-1 font-mono text-[11px] text-indigo-700 hover:bg-indigo-100 align-baseline">
          {m[1]}
        </button>
      )
    return p
  })
}

export default function Markdown({ text, onCite }) {
  const blocks = []
  let list = null
  text.split('\n').forEach((raw, i) => {
    const line = raw.trim()
    if (/^[-*•]\s+/.test(line)) {
      if (!list) { list = []; blocks.push({ type: 'ul', items: list }) }
      list.push(line.replace(/^[-*•]\s+/, ''))
      return
    }
    list = null
    if (!line) return
    if (line.startsWith('#')) blocks.push({ type: 'h', text: line.replace(/^#+\s*/, '') })
    else blocks.push({ type: 'p', text: line })
  })
  return (
    <div className="prose-case text-sm text-slate-700 leading-relaxed">
      {blocks.map((b, i) =>
        b.type === 'h' ? <h2 key={i}>{inline(b.text, onCite, i)}</h2>
          : b.type === 'ul' ? <ul key={i}>{b.items.map((it, j) => <li key={j}>{inline(it, onCite, `${i}-${j}`)}</li>)}</ul>
            : <p key={i}>{inline(b.text, onCite, i)}</p>,
      )}
    </div>
  )
}

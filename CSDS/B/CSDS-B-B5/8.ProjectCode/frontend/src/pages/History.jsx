import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Loader2, MessagesSquare, Trash2 } from 'lucide-react'
import api, { errorText } from '../api'
import { ErrorBox, Spinner } from '../components/ui.jsx'
import { downloadText, transcriptText } from './Conversation.jsx'

export default function History() {
  const [list, setList] = useState(null)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(null)
  const [loadingOne, setLoadingOne] = useState(false)
  const [deleting, setDeleting] = useState(null)

  const load = () => {
    setError('')
    api.get('/conversations').then((r) => setList(r.data)).catch((e) => { setError(errorText(e)); setList([]) })
  }
  useEffect(load, [])

  const show = async (id) => {
    setLoadingOne(true)
    setError('')
    try { setOpen((await api.get(`/conversations/${id}`)).data) } catch (e) { setError(errorText(e)) } finally { setLoadingOne(false) }
  }
  const remove = async (id) => {
    setDeleting(id)
    try {
      await api.delete(`/conversations/${id}`)
      if (open?.id === id) setOpen(null)
      load()
    } catch (e) { setError(errorText(e)) } finally { setDeleting(null) }
  }

  return (
    <div className="grid lg:grid-cols-[1fr_1.5fr] gap-6">
      <section className="space-y-3">
        <h2 className="font-semibold text-lg">Saved conversations</h2>
        <ErrorBox error={error} onRetry={load} />
        {list === null ? <Spinner /> : list.length === 0 ? (
          <div className="card p-8 text-center text-slate-500 text-sm">
            <MessagesSquare className="mx-auto mb-2 text-slate-300" />
            No saved conversations yet. <Link to="/app" className="text-indigo-600">Start one</Link> and press Save.
          </div>
        ) : (
          <ul className="space-y-2">
            {list.map((c) => (
              <li key={c.id} className={`card p-3 flex items-center gap-3 cursor-pointer hover:border-indigo-300 ${open?.id === c.id ? 'border-indigo-400' : ''}`} onClick={() => show(c.id)}>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{c.title}</div>
                  <div className="text-xs text-slate-500">{new Date(c.created_at).toLocaleString()} · {c.messages} messages</div>
                </div>
                <button className="text-slate-400 hover:text-rose-600 p-1" title="Delete" onClick={(e) => { e.stopPropagation(); remove(c.id) }}>
                  {deleting === c.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section>
        {loadingOne ? <Spinner /> : open ? (
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <h3 className="font-semibold flex-1">{open.title}</h3>
              <button className="btn-secondary !py-1 !px-2 !text-xs" onClick={() => downloadText(`${open.title}.txt`, transcriptText(open.title, open.messages))}><Download size={14} /> Download</button>
            </div>
            <div className="space-y-2">
              {open.messages.map((m) => (
                <div key={m.id} className={`flex ${m.side === 'signer' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-3 py-2 ${m.side === 'signer' ? 'bg-indigo-50 text-indigo-900' : 'bg-teal-50 text-teal-900'}`}>
                    <div className="text-[11px] opacity-70">
                      {m.side === 'signer' ? 'Signer' : 'Speaker'} · {new Date(m.created_at).toLocaleTimeString()}
                      {m.gloss && <> · {m.gloss.join(' ')}</>}
                      {m.confidence != null && <> · {Math.round(m.confidence * 100)}%</>}
                    </div>
                    <div>{m.text}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : <div className="card p-8 text-center text-sm text-slate-400">Select a conversation to read its transcript.</div>}
      </section>
    </div>
  )
}

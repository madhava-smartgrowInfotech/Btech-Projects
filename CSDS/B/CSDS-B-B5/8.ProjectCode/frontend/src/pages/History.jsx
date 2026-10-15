import { Download, MessagesSquare, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { describeError } from '../api'
import { SlideUp } from '../components/motion'
import { PageHeader } from '../components/ui/AppShell'
import { Button, IconButton } from '../components/ui/controls'
import { Card } from '../components/ui/display'
import { EmptyState, ErrorState, Modal, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { downloadText, label as pretty, stamp, transcriptText } from '../format'
import { logEvent } from '../lib/activity'

export default function History() {
  const toast = useToast()
  const [list, setList] = useState(null)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(null)
  const [loadingOne, setLoadingOne] = useState(false)
  const [confirm, setConfirm] = useState(null) // conversation row awaiting delete confirmation
  const [deleting, setDeleting] = useState(false)
  const viewer = useRef(null)

  const load = () => {
    setError(null)
    api.get('/conversations').then((r) => setList(r.data)).catch((e) => { setError(describeError(e)); setList([]) })
  }
  useEffect(load, [])

  const show = async (id) => {
    setLoadingOne(true)
    setError(null)
    try {
      setOpen((await api.get(`/conversations/${id}`)).data)
      requestAnimationFrame(() => viewer.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }))
    } catch (e) { setError(describeError(e)) } finally { setLoadingOne(false) }
  }

  const remove = async () => {
    setDeleting(true)
    try {
      await api.delete(`/conversations/${confirm.id}`)
      if (open?.id === confirm.id) setOpen(null)
      logEvent('history', `deleted “${confirm.title}”`)
      toast({ tone: 'ok', title: 'Conversation deleted', body: confirm.title })
      setConfirm(null)
      load()
    } catch (e) {
      toast({ tone: 'alert', title: 'Delete failed', body: describeError(e).message })
    } finally { setDeleting(false) }
  }

  const columns = [
    { key: 'title', label: 'Title', sortable: true, render: (c) => (
      <button type="button" onClick={() => show(c.id)} className={`max-w-[28ch] truncate text-left hover:text-ok ${open?.id === c.id ? 'text-ok' : 'text-fg'}`}>{c.title}</button>
    ) },
    { key: 'created_at', label: 'Saved', sortable: true, className: 'font-mono text-xs text-muted whitespace-nowrap', render: (c) => stamp(c.created_at) },
    { key: 'messages', label: 'Msgs', sortable: true, align: 'right', className: 'font-mono tabular-nums' },
    { key: 'actions', label: <span className="sr-only">Actions</span>, align: 'right', render: (c) => (
      <IconButton icon={Trash2} label={`Delete ${c.title}`} size="sm" onClick={() => setConfirm(c)} />
    ) },
  ]

  const rowCard = (c) => (
    <div className="panel flex items-center gap-3 p-3">
      <button type="button" onClick={() => show(c.id)} className="min-w-0 flex-1 text-left">
        <div className="truncate text-sm text-fg">{c.title}</div>
        <div className="font-mono text-[11px] text-dim">{stamp(c.created_at)} · {c.messages} msgs</div>
      </button>
      <IconButton icon={Trash2} label={`Delete ${c.title}`} size="sm" onClick={() => setConfirm(c)} />
    </div>
  )

  return (
    <>
      <PageHeader eyebrow="history" title="Saved conversations"
        subtitle="Transcripts you saved from the Conversation screen. Open one to read it, or download it as text."
        actions={<Link to="/app"><Button variant="secondary" icon={MessagesSquare}>New conversation</Button></Link>} />
      <SlideUp>
        {error && <div className="mb-4"><ErrorState title="History" error={error} onRetry={load} /></div>}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
          <Card title="conversations" eyebrow={list ? `${list.length} saved` : 'loading'}>
            <Table columns={columns} rows={list} rowKey={(c) => c.id} initialSort={{ key: 'created_at', dir: 'desc' }}
              caption="Saved conversations" cards={rowCard} pageSize={10} loading={list === null}
              empty={(
                <EmptyState icon={MessagesSquare} title="No saved conversations yet"
                  body="Hold a conversation, then press Save on the transcript to keep it here."
                  action={<Link to="/app"><Button size="sm">Start a conversation</Button></Link>} />
              )} />
          </Card>

          <div ref={viewer} className="min-w-0 scroll-mt-20">
            <Card title={open ? open.title : 'transcript'}
              action={open ? (
                <Button size="sm" variant="secondary" icon={Download} onClick={() => downloadText(`${open.title}.txt`, transcriptText(open.title, open.messages))}>Download</Button>
              ) : null}>
              {loadingOne ? (
                <div className="space-y-2"><Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-12" /></div>
              ) : open ? (
                <div className="space-y-2" role="log" aria-label={`Transcript of ${open.title}`}>
                  {open.messages.map((m) => (
                    <div key={m.id} className={`flex ${m.side === 'signer' ? 'justify-start' : 'justify-end'}`}>
                      <div className={`max-w-[88%] rounded-[6px] border px-3 py-2 ${m.side === 'signer' ? 'border-ok/30 bg-ok/[0.07]' : 'border-cyan/30 bg-cyan/[0.07]'}`}>
                        <div className="font-mono text-[10px] uppercase tracking-wider text-dim">
                          {m.side === 'signer' ? 'Signer' : 'Speaker'} · {new Date(m.created_at).toLocaleTimeString()}
                          {m.gloss && <> · {m.gloss.map(pretty).join(' ')}</>}
                          {m.confidence != null && <> · {Math.round(m.confidence * 100)}%</>}
                        </div>
                        <div className="text-sm text-fg">{m.text}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState icon={MessagesSquare} title="Nothing selected" body="Choose a conversation from the list to read its transcript." />
              )}
            </Card>
          </div>
        </div>
      </SlideUp>

      <Modal open={!!confirm} onClose={() => !deleting && setConfirm(null)} title="Delete conversation" size="sm"
        footer={(
          <>
            <Button variant="secondary" onClick={() => setConfirm(null)} disabled={deleting}>Cancel</Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={remove}>Delete</Button>
          </>
        )}>
        <p className="p-4 text-sm text-muted">“<span className="text-fg">{confirm?.title}</span>” and its {confirm?.messages} messages will be removed permanently.</p>
      </Modal>
    </>
  )
}

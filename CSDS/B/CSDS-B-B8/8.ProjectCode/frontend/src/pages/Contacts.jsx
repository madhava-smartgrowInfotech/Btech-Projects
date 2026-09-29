import { useEffect, useState } from 'react'
import { CheckCircle2, Loader2, Pencil, Plus, Search, Trash2, TriangleAlert } from 'lucide-react'
import api, { errMsg } from '../api.js'
import { ErrorBox, PageTitle, Spinner } from '../components/ui.jsx'

const EMPTY = { name: '', relation: '', email: '', telegram_chat_id: '', active: true }

function ContactForm({ initial, onSaved, onCancel }) {
  const [f, setF] = useState(initial || EMPTY)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const save = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      if (f.id) await api.put(`/contacts/${f.id}`, f)
      else await api.post('/contacts', f)
      onSaved()
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={save} className="grid sm:grid-cols-2 gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
      <div><label className="label">Name</label><input className="input" value={f.name} onChange={set('name')} required /></div>
      <div><label className="label">Relation</label><input className="input" value={f.relation} onChange={set('relation')} placeholder="Daughter, neighbour, nurse..." /></div>
      <div><label className="label">Email</label><input className="input" type="email" value={f.email} onChange={set('email')} /></div>
      <div><label className="label">Telegram chat ID</label><input className="input" value={f.telegram_chat_id} onChange={set('telegram_chat_id')} placeholder="e.g. 123456789" /></div>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.active} onChange={set('active')} /> Receives alerts</label>
      <div className="sm:col-span-2"><ErrorBox error={error} /></div>
      <div className="sm:col-span-2 flex gap-2">
        <button className="btn btn-primary" disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Save contact</button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

function Settings({ settings, onSaved }) {
  const [f, setF] = useState(settings)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  useEffect(() => setF(settings), [settings])
  const set = (k) => (e) => { setSaved(false); setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }) }
  const save = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const { channels, monitor_running, ...body } = f
      const { data } = await api.put('/settings', body)
      onSaved(data); setSaved(true)
    } catch (err) { setError(errMsg(err)) } finally { setBusy(false) }
  }
  return (
    <form onSubmit={save} className="card p-5 space-y-4">
      <h2 className="font-semibold text-slate-900">Monitoring settings</h2>
      <div><label className="label">Room name</label><input className="input" value={f.room_name} onChange={set('room_name')} /></div>
      <div>
        <label className="label">Camera source</label>
        <input className="input" value={f.camera_source} onChange={set('camera_source')} />
        <p className="text-xs text-slate-500 mt-1">0 = webcam; phone: http://PHONE-IP:8080/video (IP Webcam app).</p>
      </div>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.privacy_mode} onChange={set('privacy_mode')} /> Privacy mode - show only the skeleton</label>
      <div>
        <label className="label">Low-light enhancement</label>
        <select className="input" value={f.low_light} onChange={set('low_light')}>
          <option value="auto">Automatic (when the room is dim)</option>
          <option value="on">Always on</option>
          <option value="off">Off</option>
        </select>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div><label className="label">Confirm fall (s)</label><input className="input" type="number" step="0.5" value={f.confirm_seconds} onChange={set('confirm_seconds')} /></div>
        <div><label className="label">'I'm OK' countdown (s)</label><input className="input" type="number" value={f.countdown_seconds} onChange={set('countdown_seconds')} /></div>
        <div><label className="label">Inactivity warning (min)</label><input className="input" type="number" step="0.5" value={f.inactivity_minutes} onChange={set('inactivity_minutes')} /></div>
      </div>
      <ErrorBox error={error} />
      <div className="flex items-center gap-3">
        <button className="btn btn-primary" disabled={busy}>{busy && <Loader2 className="w-4 h-4 animate-spin" />} Save settings</button>
        {saved && <span className="text-sm text-green-700 flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Saved</span>}
      </div>
    </form>
  )
}

export default function Contacts() {
  const [contacts, setContacts] = useState(null)
  const [settings, setSettings] = useState(null)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [chats, setChats] = useState(null)
  const [chatBusy, setChatBusy] = useState(false)
  const [chatErr, setChatErr] = useState('')

  const load = async () => {
    try {
      const [c, s] = await Promise.all([api.get('/contacts'), api.get('/settings')])
      setContacts(c.data); setSettings(s.data); setError('')
    } catch (e) { setError(errMsg(e)) }
  }
  useEffect(() => { load() }, [])

  const remove = async (id) => {
    try { await api.delete(`/contacts/${id}`); load() } catch (e) { setError(errMsg(e)) }
  }
  const findChats = async () => {
    setChatBusy(true); setChatErr('')
    try { const { data } = await api.get('/telegram/chats'); setChats(data) } catch (e) { setChatErr(errMsg(e)) } finally { setChatBusy(false) }
  }

  if (!contacts && !error) return <Spinner />
  const ch = settings?.channels
  return (
    <div>
      <PageTitle title="Contacts & settings" subtitle="Who gets emergency alerts, and how monitoring behaves" />
      <ErrorBox error={error} onRetry={load} />
      {ch && (
        <div className="grid sm:grid-cols-2 gap-3 my-4">
          {[['Telegram', ch.telegram, 'TELEGRAM_BOT_TOKEN'], ['Email (Gmail)', ch.email, 'SMTP_USER and SMTP_PASSWORD']].map(([n, ok, keys]) => (
            <div key={n} className={`rounded-lg border px-4 py-3 text-sm flex items-start gap-2 ${ok ? 'border-green-200 bg-green-50 text-green-800' : 'border-amber-200 bg-amber-50 text-amber-800'}`}>
              {ok ? <CheckCircle2 className="w-4 h-4 mt-0.5" /> : <TriangleAlert className="w-4 h-4 mt-0.5" />}
              <div><b>{n}</b> {ok ? 'is configured.' : `is not configured - set ${keys} in .env and restart.`}</div>
            </div>
          ))}
        </div>
      )}
      <div className="grid lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-900">Emergency contacts</h2>
            {editing === null && <button className="btn btn-primary" onClick={() => setEditing(EMPTY)}><Plus className="w-4 h-4" /> Add contact</button>}
          </div>
          {editing && <div className="mb-4"><ContactForm initial={editing} onSaved={() => { setEditing(null); load() }} onCancel={() => setEditing(null)} /></div>}
          {contacts?.length === 0 && !editing && <p className="text-sm text-slate-500 py-6 text-center">No contacts yet - add family members or caregivers who should receive alerts.</p>}
          <div className="divide-y divide-slate-100">
            {contacts?.map((c) => (
              <div key={c.id} className="py-3 flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-semibold">{c.name[0]?.toUpperCase()}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-slate-900">{c.name} {c.relation && <span className="text-slate-500 font-normal">- {c.relation}</span>} {!c.active && <span className="text-xs text-slate-400">(paused)</span>}</div>
                  <div className="text-xs text-slate-500 truncate">{[c.email, c.telegram_chat_id && `Telegram ${c.telegram_chat_id}`].filter(Boolean).join(' - ')}</div>
                </div>
                <button className="p-2 text-slate-500 hover:text-slate-800" onClick={() => setEditing(c)} aria-label="Edit"><Pencil className="w-4 h-4" /></button>
                <button className="p-2 text-slate-500 hover:text-red-600" onClick={() => remove(c.id)} aria-label="Delete"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
          </div>
          <div className="mt-5 border-t border-slate-100 pt-4">
            <div className="text-sm font-medium text-slate-800">Find Telegram chat IDs</div>
            <p className="text-xs text-slate-500 mt-0.5">Ask each contact to open your bot in Telegram and send it any message, then press the button.</p>
            <button className="btn btn-secondary mt-2" onClick={findChats} disabled={chatBusy}>
              {chatBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Look up chats
            </button>
            <div className="mt-2"><ErrorBox error={chatErr} /></div>
            {chats && (chats.length === 0
              ? <p className="text-sm text-slate-500 mt-2">No messages yet - send the bot a message first.</p>
              : <ul className="mt-2 text-sm space-y-1">{chats.map((c) => (
                <li key={c.chat_id} className="flex items-center gap-2">
                  <code className="bg-slate-100 px-1.5 rounded">{c.chat_id}</code> {c.name} {c.username && `(@${c.username})`}
                  <button className="text-teal-700 underline text-xs" onClick={() => setEditing({ ...EMPTY, name: c.name, telegram_chat_id: c.chat_id })}>Add as contact</button>
                </li>))}</ul>)}
          </div>
        </div>
        <div className="lg:col-span-2">{settings && <Settings settings={settings} onSaved={setSettings} />}</div>
      </div>
    </div>
  )
}

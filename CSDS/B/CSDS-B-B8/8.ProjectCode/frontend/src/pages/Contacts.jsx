import { useEffect, useState } from 'react'
import { CheckCircle2, Pencil, Plus, Search, Trash2, TriangleAlert, UserPlus, Users } from 'lucide-react'
import {
  Badge, Button, Card, CardHeader, Checkbox, EmptyState, ErrorState, IconButton, Input, Modal, PageHeader, Select, Skeleton, Switch, Table, useToast,
} from '../components/ui'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const EMPTY = { name: '', relation: '', email: '', telegram_chat_id: '', active: true }

function ContactForm({ initial, onSaved, onCancel }) {
  const toast = useToast()
  const [f, setF] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { name: f.name, relation: f.relation, email: f.email, telegram_chat_id: f.telegram_chat_id, active: f.active }
      if (f.id) await api.put(`/contacts/${f.id}`, body)
      else await api.post('/contacts', body)
      toast({ title: f.id ? 'Contact updated' : 'Contact added', message: f.name })
      onSaved()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <form id="contact-form" onSubmit={save} className="stack" style={{ gap: 14 }}>
      <div className="form-grid">
        <Input label="Name" value={f.name} onChange={set('name')} required data-autofocus />
        <Input label="Relation" value={f.relation} onChange={set('relation')} placeholder="Daughter, neighbour, nurse…" />
        <Input label="Email" type="email" value={f.email} onChange={set('email')} />
        <Input label="Telegram chat ID" value={f.telegram_chat_id} onChange={set('telegram_chat_id')} placeholder="e.g. 123456789" />
        <div className="full">
          <Checkbox label="Receives alerts" checked={f.active} onChange={set('active')} />
        </div>
      </div>
      <p className="faint">Add an email, a Telegram chat ID or both so alerts can reach this contact.</p>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <div className="row" style={{ justifyContent: 'flex-end' }}>
        <Button onClick={onCancel}>Cancel</Button>
        <Button type="submit" variant="primary" loading={busy}>
          Save contact
        </Button>
      </div>
    </form>
  )
}

const LIMITS = { countdown_seconds: [5, 300], confirm_seconds: [1, 30], inactivity_minutes: [0.5, 720] }

function SettingsForm({ settings, onSaved }) {
  const toast = useToast()
  const [f, setF] = useState(settings)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => setF(settings), [settings])
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const save = async (e) => {
    e.preventDefault()
    for (const [k, [lo, hi]] of Object.entries(LIMITS)) {
      const v = Number(f[k])
      if (!(v >= lo && v <= hi)) {
        setError(`${k.replace('_', ' ')} must be between ${lo} and ${hi}.`)
        return
      }
    }
    setBusy(true)
    setError('')
    try {
      const body = {
        room_name: f.room_name,
        camera_source: f.camera_source,
        privacy_mode: !!f.privacy_mode,
        low_light: f.low_light,
        confirm_seconds: Number(f.confirm_seconds),
        countdown_seconds: Number(f.countdown_seconds),
        inactivity_minutes: Number(f.inactivity_minutes),
      }
      const data = await api.put('/settings', body)
      onSaved(data)
      toast({ title: 'Settings saved', message: 'Monitoring uses them straight away.' })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Monitoring settings" subtitle="How the camera, privacy and alert timing behave." />
      <form className="card-body stack" style={{ gap: 14 }} onSubmit={save}>
        <Input label="Room name" value={f.room_name} onChange={set('room_name')} />
        <Input label="Camera source" value={f.camera_source} onChange={set('camera_source')} mono hint="0 = webcam; phone: http://PHONE-IP:8080/video (IP Webcam app)." />
        <Switch label="Privacy mode - show only the skeleton" checked={!!f.privacy_mode} onChange={set('privacy_mode')} />
        <Select
          label="Low-light enhancement"
          value={f.low_light}
          onChange={set('low_light')}
          options={[
            { value: 'auto', label: 'Automatic (when the room is dim)' },
            { value: 'on', label: 'Always on' },
            { value: 'off', label: 'Off' },
          ]}
        />
        <div className="form-grid-3">
          <Input label="Confirm fall (s)" type="number" step="0.5" min={1} max={30} value={f.confirm_seconds} onChange={set('confirm_seconds')} />
          <Input label="'I'm OK' countdown (s)" type="number" min={5} max={300} value={f.countdown_seconds} onChange={set('countdown_seconds')} />
          <Input label="Inactivity warning (min)" type="number" step="0.5" min={0.5} max={720} value={f.inactivity_minutes} onChange={set('inactivity_minutes')} />
        </div>
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
        <div>
          <Button type="submit" variant="primary" loading={busy}>
            Save settings
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default function Contacts() {
  const toast = useToast()
  const contacts = useAsync(() => api.get('/contacts'), [])
  const settings = useAsync(() => api.get('/settings'), [])
  const [editing, setEditing] = useState(null)
  const [removing, setRemoving] = useState(null)
  const [removeBusy, setRemoveBusy] = useState(false)
  const [chats, setChats] = useState(null)
  const [chatBusy, setChatBusy] = useState(false)
  const [chatErr, setChatErr] = useState('')

  const remove = async () => {
    setRemoveBusy(true)
    try {
      await api.del(`/contacts/${removing.id}`)
      toast({ title: 'Contact removed', message: removing.name })
      setRemoving(null)
      contacts.reload({ quiet: true })
    } catch (e) {
      toast({ title: "Couldn't remove contact", message: e.message, tone: 'error' })
    } finally {
      setRemoveBusy(false)
    }
  }
  const findChats = async () => {
    setChatBusy(true)
    setChatErr('')
    try {
      setChats(await api.get('/telegram/chats'))
    } catch (e) {
      setChatErr(e.message)
    } finally {
      setChatBusy(false)
    }
  }

  const ch = settings.data?.channels
  const columns = [
    {
      key: 'name',
      label: 'Contact',
      sortValue: (c) => c.name.toLowerCase(),
      render: (c) => (
        <div className="row" style={{ flexWrap: 'nowrap' }}>
          <span className="avatar" aria-hidden="true">{c.name[0]?.toUpperCase()}</span>
          <div style={{ minWidth: 0 }}>
            <strong>{c.name}</strong>
            {c.relation && <div className="faint">{c.relation}</div>}
          </div>
        </div>
      ),
    },
    {
      key: 'reach',
      label: 'Reach',
      sortable: false,
      render: (c) => [c.email, c.telegram_chat_id && `Telegram ${c.telegram_chat_id}`].filter(Boolean).join(' · '),
    },
    { key: 'active', label: 'Alerts', sortValue: (c) => (c.active ? 1 : 0), render: (c) => <Badge tone={c.active ? 'safe' : 'neutral'} dot>{c.active ? 'On' : 'Paused'}</Badge> },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (c) => (
        <div className="row" style={{ flexWrap: 'nowrap', gap: 2 }}>
          <IconButton icon={Pencil} label={`Edit ${c.name}`} size="sm" onClick={() => setEditing(c)} />
          <IconButton icon={Trash2} label={`Delete ${c.name}`} size="sm" onClick={() => setRemoving(c)} />
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Contacts & settings"
        description="Who gets emergency alerts, and how monitoring behaves."
        actions={
          <Button variant="primary" icon={Plus} onClick={() => setEditing(EMPTY)}>
            Add contact
          </Button>
        }
      />

      {ch && (
        <div className="grid grid-2" style={{ marginBottom: 18 }}>
          {[
            ['Telegram', ch.telegram, 'TELEGRAM_BOT_TOKEN'],
            ['Email (Gmail)', ch.email, 'SMTP_USER and SMTP_PASSWORD'],
          ].map(([name, ok, keys]) => (
            <div key={name} className={`notice ${ok ? 'safe' : 'warn'}`}>
              {ok ? <CheckCircle2 size={18} aria-hidden="true" /> : <TriangleAlert size={18} aria-hidden="true" />}
              <div>
                <strong>{name}</strong> {ok ? 'is configured.' : <>is not configured - set <code>{keys}</code> in <code>.env</code> and restart.</>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Stagger className="split" gap={0.08}>
        <div className="stack">
          <Card>
            <CardHeader title="Emergency contacts" subtitle="Everyone marked on receives the Telegram message and email." />
            {contacts.error && !contacts.data ? (
              <ErrorState title="Couldn't load contacts" error={contacts.error} onRetry={contacts.reload} />
            ) : (
              <Table
                caption="Emergency contacts"
                columns={columns}
                rows={contacts.data}
                rowKey={(c) => c.id}
                loading={contacts.loading && !contacts.data}
                pageSize={8}
                empty={
                  <EmptyState icon={Users} title="No contacts yet" actions={<Button variant="primary" icon={UserPlus} onClick={() => setEditing(EMPTY)}>Add the first contact</Button>}>
                    Add family members or caregivers who should be alerted when a fall is confirmed.
                  </EmptyState>
                }
              />
            )}
          </Card>

          <Card>
            <CardHeader title="Find Telegram chat IDs" subtitle="Ask each contact to open your bot in Telegram and send it any message, then look up chats." />
            <div className="card-body stack" style={{ gap: 12 }}>
              <div>
                <Button icon={Search} onClick={findChats} loading={chatBusy}>
                  Look up chats
                </Button>
              </div>
              {chatErr && (
                <p className="field-error" role="alert">
                  {chatErr}
                </p>
              )}
              {chats &&
                (chats.length === 0 ? (
                  <p className="faint">No messages yet - ask the contact to send your bot a message first.</p>
                ) : (
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 10 }}>
                    {chats.map((c) => (
                      <li key={c.chat_id} className="row">
                        <code>{c.chat_id}</code>
                        <span>
                          {c.name} {c.username && <span className="faint">(@{c.username})</span>}
                        </span>
                        <Button size="sm" onClick={() => setEditing({ ...EMPTY, name: c.name, telegram_chat_id: String(c.chat_id) })}>
                          Add as contact
                        </Button>
                      </li>
                    ))}
                  </ul>
                ))}
            </div>
          </Card>
        </div>

        {settings.error && !settings.data ? (
          <ErrorState title="Couldn't load settings" error={settings.error} onRetry={settings.reload} />
        ) : settings.data ? (
          <SettingsForm settings={settings.data} onSaved={() => settings.reload({ quiet: true })} />
        ) : (
          <Skeleton height={420} />
        )}
      </Stagger>

      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing?.id ? 'Edit contact' : 'Add contact'}>
        {editing && (
          <ContactForm
            key={editing.id ?? 'new'}
            initial={editing}
            onCancel={() => setEditing(null)}
            onSaved={() => {
              setEditing(null)
              contacts.reload({ quiet: true })
            }}
          />
        )}
      </Modal>

      <Modal
        open={!!removing}
        onClose={() => setRemoving(null)}
        title="Remove this contact?"
        footer={
          <>
            <Button onClick={() => setRemoving(null)}>Keep contact</Button>
            <Button variant="danger" loading={removeBusy} onClick={remove}>
              Remove
            </Button>
          </>
        }
      >
        <p>
          <strong>{removing?.name}</strong> will no longer receive fall alerts.
        </p>
      </Modal>
    </div>
  )
}

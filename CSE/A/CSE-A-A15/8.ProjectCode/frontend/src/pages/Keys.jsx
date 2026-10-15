import { useEffect, useRef, useState } from 'react'
import { Copy, Download, KeyRound, Plus, Trash2, Upload } from 'lucide-react'
import api, { describeError, saveText } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button, IconButton, Input, Select, Textarea } from '../components/ui/controls'
import { Badge, Card } from '../components/ui/display'
import { EmptyState, ErrorState, Modal, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'

const SIZES = [['2048', 'RSA 2048 (fast)'], ['3072', 'RSA 3072 (recommended)'], ['4096', 'RSA 4096 (slow to generate)']]

export default function Keys() {
  const toast = useToast()
  const nameRef = useRef(null)
  const [keys, setKeys] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState('')
  const [name, setName] = useState('My receiving key')
  const [bits, setBits] = useState('3072')
  const [impName, setImpName] = useState('')
  const [impPem, setImpPem] = useState('')
  const [confirm, setConfirm] = useState(null)

  const load = () => {
    setError(null)
    return api.get('/keys').then((r) => setKeys(r.data)).catch((e) => setError(describeError(e)))
  }
  useEffect(() => { load() }, [])

  // one place for every key action: busy state, success toast, failure toast, then reload the list
  async function run(label, fn, okTitle) {
    setBusy(label)
    try {
      await fn()
      toast({ tone: 'ok', title: okTitle })
      await load()
    } catch (e) {
      const d = describeError(e)
      toast({ tone: 'alert', title: 'Action failed', body: [d.message, d.hint].filter(Boolean).join(' ') })
    } finally {
      setBusy('')
    }
  }

  const generate = (e) => {
    e.preventDefault()
    run('gen', () => api.post('/keys/generate', { name, bits: Number(bits) }),
      'Keypair generated. The private key stays on this machine.')
  }
  const doImport = (e) => {
    e.preventDefault()
    run('imp', async () => {
      await api.post('/keys/import', { name: impName, pem: impPem })
      setImpPem('')
      setImpName('')
    }, 'Key imported')
  }
  const exportPart = (k, part) => run(`exp${k.id}${part}`, async () => {
    const { data } = await api.get(`/keys/${k.id}/export`, { params: { part }, responseType: 'text', transformResponse: (d) => d })
    saveText(data, `${k.name.replace(/\W+/g, '_')}_${part}.pem`)
  }, `${part === 'private' ? 'Private' : 'Public'} key downloaded`)
  const copyPub = (k) => navigator.clipboard.writeText(k.public_pem).then(
    () => toast({ tone: 'ok', title: 'Public key copied' }),
    () => toast({ tone: 'alert', title: 'Copy failed', body: 'Use Download instead.' }),
  )
  const remove = async (k) => {
    await run(`del${k.id}`, () => api.delete(`/keys/${k.id}`), 'Key deleted')
    setConfirm(null)
  }

  const actions = (k) => (
    <div className="flex justify-end gap-1">
      <IconButton size="sm" icon={Copy} label={`Copy public key of ${k.name}`} onClick={() => copyPub(k)} />
      <IconButton size="sm" icon={Download} label={`Download public key of ${k.name}`} disabled={busy === `exp${k.id}public`}
        onClick={() => exportPart(k, 'public')} />
      {k.has_private && (
        <IconButton size="sm" icon={KeyRound} label={`Download private key of ${k.name} (keep it secret)`}
          disabled={busy === `exp${k.id}private`} onClick={() => exportPart(k, 'private')} />
      )}
      <IconButton size="sm" icon={Trash2} label={`Delete ${k.name}`} variant="danger" onClick={() => setConfirm(k)} />
    </div>
  )

  const columns = [
    { key: 'name', label: 'Name', sortable: true, render: (k) => <span className="font-medium text-fg">{k.name}</span> },
    { key: 'type', label: 'Type', render: (k) => (k.has_private ? <Badge tone="ok">keypair</Badge> : <Badge>public only</Badge>) },
    { key: 'bits', label: 'Size', align: 'right', sortable: true, render: (k) => `${k.bits}-bit` },
    { key: 'fingerprint', label: 'Fingerprint', className: 'font-mono text-xs text-muted break-all' },
    { key: 'actions', label: 'Actions', align: 'right', render: actions },
  ]

  return (
    <>
      <PageHeader title="Keys"
        subtitle="Generate an RSA keypair, then give the public half to anyone who should send you something. Private keys never leave this machine unless you export them." />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Generate a keypair" eyebrow="receive">
          <form onSubmit={generate} className="space-y-4">
            <Input ref={nameRef} label="Name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={60} />
            <Select label="Key size" value={bits} onChange={(e) => setBits(e.target.value)} options={SIZES} />
            <Button type="submit" icon={Plus} loading={busy === 'gen'}>Generate</Button>
          </form>
        </Card>

        <Card title="Import a key" eyebrow="send or receive">
          <form onSubmit={doImport} className="space-y-4">
            <p className="text-xs text-muted">
              Paste a recipient's <b className="text-fg">public</b> key to send to them, or your own unencrypted RSA <b className="text-fg">private</b> key to receive.
            </p>
            <Input label="Name" value={impName} onChange={(e) => setImpName(e.target.value)} required maxLength={60} placeholder="e.g. Alex (public)" />
            <Textarea label="PEM" rows={5} value={impPem} onChange={(e) => setImpPem(e.target.value)} required
              placeholder="-----BEGIN PUBLIC KEY-----" className="font-mono text-xs" />
            <Button type="submit" variant="secondary" icon={Upload} loading={busy === 'imp'}>Import</Button>
          </form>
        </Card>
      </div>

      {error && <div className="mt-4"><ErrorState error={error} onRetry={load} /></div>}

      <div className="mt-4">
        <Card title="Your keys" bodyClass="px-4 pb-2 pt-0">
          <Table
            caption="Keys you hold and recipients you can send to"
            columns={columns}
            rows={error ? null : keys}
            rowKey={(k) => k.id}
            loading={keys === null && !error}
            initialSort={{ key: 'name', dir: 'asc' }}
            cards={(k) => (
              <div className="panel p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-fg">{k.name}</span>
                  {k.has_private ? <Badge tone="ok">keypair</Badge> : <Badge>public only</Badge>}
                </div>
                <div className="mt-1 font-mono text-xs text-muted">{k.bits}-bit · {k.fingerprint}</div>
                <div className="mt-2">{actions(k)}</div>
              </div>
            )}
            empty={!error && (
              <EmptyState icon={KeyRound} title="No keys yet"
                body="Generate a keypair to receive files, or import a recipient's public key to send to them."
                action={<Button size="sm" icon={Plus} onClick={() => nameRef.current?.focus()}>Generate a keypair</Button>} />
            )}
          />
        </Card>
      </div>

      <Modal open={!!confirm} onClose={() => setConfirm(null)} title="Delete key" size="sm"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>Cancel</Button>
            <Button variant="danger" icon={Trash2} loading={busy === `del${confirm?.id}`} onClick={() => remove(confirm)}>Delete</Button>
          </>
        )}>
        <p className="p-4 text-sm text-muted">
          Delete <b className="text-fg">{confirm?.name}</b>? Messages sent to this key can no longer be opened. This cannot be undone.
        </p>
      </Modal>
    </>
  )
}

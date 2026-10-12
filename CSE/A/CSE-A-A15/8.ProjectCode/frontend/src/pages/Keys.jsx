import { useEffect, useState } from 'react'
import { Copy, Download, KeyRound, Plus, Trash2, Upload } from 'lucide-react'
import api, { errText, saveText } from '../api'
import { Badge, ErrorBox, Notice, PageHead, Spinner } from '../components/ui'

export default function Keys() {
  const [keys, setKeys] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState('')
  const [name, setName] = useState('My receiving key')
  const [bits, setBits] = useState(3072)
  const [impName, setImpName] = useState('')
  const [impPem, setImpPem] = useState('')

  const load = () => api.get('/keys').then((r) => setKeys(r.data)).catch((e) => setError(errText(e)))
  useEffect(() => { load() }, [])

  async function run(label, fn, okMsg) {
    setBusy(label)
    setError('')
    setNotice('')
    try {
      await fn()
      if (okMsg) setNotice(okMsg)
      await load()
    } catch (e) {
      setError(errText(e))
    } finally {
      setBusy('')
    }
  }

  const generate = (e) => {
    e.preventDefault()
    run('gen', () => api.post('/keys/generate', { name, bits: Number(bits) }), 'Keypair generated. The private key stays on this machine.')
  }
  const doImport = (e) => {
    e.preventDefault()
    run('imp', async () => { await api.post('/keys/import', { name: impName, pem: impPem }); setImpPem(''); setImpName('') }, 'Key imported.')
  }
  const exportPart = (k, part) => run(`exp${k.id}${part}`, async () => {
    const { data } = await api.get(`/keys/${k.id}/export`, { params: { part }, responseType: 'text', transformResponse: (d) => d })
    saveText(data, `${k.name.replace(/\W+/g, '_')}_${part}.pem`)
  })
  const copyPub = (k) => navigator.clipboard.writeText(k.public_pem).then(() => setNotice('Public key copied.'), () => setError('Copy failed - use Download instead.'))
  const remove = (k) => {
    if (window.confirm(`Delete "${k.name}"? Messages sent to this key can no longer be opened.`)) {
      run(`del${k.id}`, () => api.delete(`/keys/${k.id}`), 'Key deleted.')
    }
  }

  return (
    <>
      <PageHead icon={KeyRound} title="Keys"
        sub="Generate an RSA keypair, then give the public half to anyone who should send you something. Private keys never leave this machine unless you export them." />
      <div className="mb-4 space-y-2"><ErrorBox>{error}</ErrorBox><Notice>{notice}</Notice></div>

      <div className="grid gap-4 lg:grid-cols-2">
        <form onSubmit={generate} className="card space-y-3">
          <h2 className="flex items-center gap-2"><Plus className="h-4 w-4" /> Generate a keypair</h2>
          <div><label className="label" htmlFor="kn">Name</label>
            <input id="kn" className="input" value={name} onChange={(e) => setName(e.target.value)} required maxLength={60} /></div>
          <div><label className="label" htmlFor="kb">Key size</label>
            <select id="kb" className="input" value={bits} onChange={(e) => setBits(e.target.value)}>
              <option value={2048}>RSA 2048 (fast)</option>
              <option value={3072}>RSA 3072 (recommended)</option>
              <option value={4096}>RSA 4096 (slow to generate)</option>
            </select></div>
          <button className="btn-primary" disabled={busy === 'gen'}>{busy === 'gen' ? <Spinner text="Generating..." /> : 'Generate'}</button>
        </form>

        <form onSubmit={doImport} className="card space-y-3">
          <h2 className="flex items-center gap-2"><Upload className="h-4 w-4" /> Import a key</h2>
          <p className="text-xs text-slate-500">Paste a recipient's <b>public</b> key to send to them, or your own unencrypted RSA <b>private</b> key (PEM) to receive.</p>
          <div><label className="label" htmlFor="in">Name</label>
            <input id="in" className="input" value={impName} onChange={(e) => setImpName(e.target.value)} required maxLength={60} placeholder="e.g. Alex (public)" /></div>
          <div><label className="label" htmlFor="ip">PEM</label>
            <textarea id="ip" className="input h-24 font-mono text-xs" value={impPem} onChange={(e) => setImpPem(e.target.value)} required placeholder="-----BEGIN PUBLIC KEY-----" /></div>
          <button className="btn-ghost" disabled={busy === 'imp'}>{busy === 'imp' ? <Spinner text="Importing..." /> : 'Import'}</button>
        </form>
      </div>

      <div className="card mt-4 overflow-x-auto p-0">
        <table className="w-full">
          <thead className="border-b border-slate-200"><tr>
            <th className="th">Name</th><th className="th">Type</th><th className="th">Size</th><th className="th">Fingerprint</th><th className="th text-right">Actions</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {keys === null && <tr><td className="td" colSpan={5}><Spinner text="Loading keys..." /></td></tr>}
            {keys?.length === 0 && <tr><td className="td text-slate-500" colSpan={5}>No keys yet. Generate one above.</td></tr>}
            {keys?.map((k) => (
              <tr key={k.id}>
                <td className="td font-medium">{k.name}</td>
                <td className="td">{k.has_private ? <Badge tone="good">keypair</Badge> : <Badge>public only</Badge>}</td>
                <td className="td">{k.bits}</td>
                <td className="td font-mono text-xs">{k.fingerprint}</td>
                <td className="td">
                  <div className="flex justify-end gap-1">
                    <button className="btn-ghost !px-2 !py-1" title="Copy public key" onClick={() => copyPub(k)}><Copy className="h-4 w-4" /></button>
                    <button className="btn-ghost !px-2 !py-1" title="Download public key" onClick={() => exportPart(k, 'public')}><Download className="h-4 w-4" /> Public</button>
                    {k.has_private && <button className="btn-ghost !px-2 !py-1" title="Download private key - keep it secret"
                      disabled={busy === `exp${k.id}private`} onClick={() => exportPart(k, 'private')}><Download className="h-4 w-4" /> Private</button>}
                    <button className="btn-danger !px-2 !py-1" title="Delete" onClick={() => remove(k)}><Trash2 className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

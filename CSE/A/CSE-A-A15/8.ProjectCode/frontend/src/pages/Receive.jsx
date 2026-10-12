import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, Download, ShieldCheck, XCircle } from 'lucide-react'
import api, { download, errText, fmtBytes, fmtMs } from '../api'
import { Badge, ErrorBox, HashLine, PageHead, Spinner, Timings } from '../components/ui'

export default function Receive() {
  const [params] = useSearchParams()
  const [keys, setKeys] = useState([])
  const [sent, setSent] = useState([])
  const [keyId, setKeyId] = useState('')
  const [mode, setMode] = useState(params.get('op') ? 'sent' : 'upload')
  const [file, setFile] = useState(null)
  const [fromOp, setFromOp] = useState(params.get('op') || '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    Promise.all([api.get('/keys'), api.get('/log', { params: { op: 'send', limit: 50 } })])
      .then(([k, l]) => {
        const own = k.data.filter((x) => x.has_private)
        setKeys(own)
        if (own[0]) setKeyId(String(own[0].id))
        const ok = l.data.filter((x) => x.ok)
        setSent(ok)
        if (!params.get('op') && ok[0]) setFromOp(String(ok[0].id))
        const wanted = ok.find((x) => String(x.id) === params.get('op'))
        if (wanted) setKeyId(String(wanted.details.key_id))
      })
      .catch((e) => setError(errText(e)))
  }, [])

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    const fd = new FormData()
    fd.append('key_id', keyId)
    if (mode === 'upload') fd.append('stego', file); else fd.append('from_op', fromOp)
    try {
      const { data } = await api.post('/receive', fd)
      setResult(data)
    } catch (err) {
      setError(errText(err))
    } finally {
      setBusy(false)
    }
  }

  const ready = keyId && (mode === 'upload' ? file : fromOp)

  return (
    <>
      <PageHead icon={ShieldCheck} title="Receive" sub="Extract the hidden bundle from a stego image, unwrap the session key with your private key, verify the AES-GCM tag and restore the file." />
      <div className="grid gap-4 lg:grid-cols-5">
        <form onSubmit={submit} className="card space-y-4 lg:col-span-2">
          <div>
            <label className="label" htmlFor="pk">Your private key</label>
            <select id="pk" className="input" value={keyId} onChange={(e) => setKeyId(e.target.value)} required>
              {keys.length === 0 && <option value="">No keypairs - create one on the Keys page</option>}
              {keys.map((k) => <option key={k.id} value={k.id}>{k.name} ({k.bits}-bit)</option>)}
            </select>
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between"><span className="label !mb-0">Stego image</span>
              <button type="button" className="text-xs text-brand-700 hover:underline" onClick={() => setMode(mode === 'upload' ? 'sent' : 'upload')}>
                {mode === 'upload' ? 'Pick one I sent' : 'Upload a file'}</button></div>
            {mode === 'upload' ? (
              <input type="file" aria-label="Stego image" accept="image/png,image/*" className="input" onChange={(e) => setFile(e.target.files[0] || null)} />
            ) : (
              <select className="input" aria-label="Sent image" value={fromOp} onChange={(e) => setFromOp(e.target.value)}>
                {sent.length === 0 && <option value="">Nothing sent yet</option>}
                {sent.map((s) => <option key={s.id} value={s.id}>#{s.id} - {s.details.filename} in {s.details.cover}</option>)}
              </select>
            )}
          </div>
          <ErrorBox>{error}</ErrorBox>
          <button className="btn-primary w-full" disabled={busy || !ready}>
            {busy ? <Spinner text="Extracting and decrypting..." /> : 'Extract and decrypt'}
          </button>
        </form>

        <div className="card lg:col-span-3">
          {!result && <p className="text-sm text-slate-500">The restored file and its hash comparison appear here.</p>}
          {result && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                {result.hash_match ? <CheckCircle2 className="h-6 w-6 text-brand-600" /> : <XCircle className="h-6 w-6 text-red-600" />}
                <h2>{result.hash_match ? 'Restored byte for byte' : 'Hash mismatch'}</h2>
                <Badge tone="good">AES-GCM tag verified</Badge>
              </div>
              <div className="text-sm text-slate-600"><b>{result.filename}</b> - {fmtBytes(result.output_bytes)}</div>
              <div className="grid gap-3 sm:grid-cols-2">
                <HashLine label="SHA-256 recorded at send time" value={result.embedded_sha256} ok={result.hash_match} />
                <HashLine label="SHA-256 of the restored file" value={result.output_sha256} ok={result.hash_match} />
              </div>
              <button className="btn-primary" onClick={() => download(`/ops/${result.op_id}/restored`, result.filename)}>
                <Download className="h-4 w-4" /> Download {result.filename}
              </button>
              <Timings items={[['Extract', fmtMs(result.timings_ms.extract)], ['Decrypt', fmtMs(result.timings_ms.decrypt)],
                ['Bundle', fmtBytes(result.bundle_bytes)], ['File', fmtBytes(result.output_bytes)]]} />
            </div>
          )}
        </div>
      </div>
    </>
  )
}

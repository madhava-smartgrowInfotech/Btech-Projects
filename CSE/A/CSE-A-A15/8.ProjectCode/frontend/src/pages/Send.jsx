import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Send as SendIcon } from 'lucide-react'
import api, { download, errText, fmtBytes, fmtMs } from '../api'
import { AuthImage, ErrorBox, HashLine, PageHead, Spinner, Stat, Timings } from '../components/ui'

export default function Send() {
  const [keys, setKeys] = useState([])
  const [covers, setCovers] = useState([])
  const [payloads, setPayloads] = useState([])
  const [keyId, setKeyId] = useState('')
  const [payloadMode, setPayloadMode] = useState('sample')
  const [payloadSample, setPayloadSample] = useState('')
  const [payloadFile, setPayloadFile] = useState(null)
  const [coverMode, setCoverMode] = useState('sample')
  const [coverSample, setCoverSample] = useState('')
  const [coverFile, setCoverFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  useEffect(() => {
    Promise.all([api.get('/keys'), api.get('/samples/covers'), api.get('/samples/payloads')])
      .then(([k, c, p]) => {
        setKeys(k.data); setCovers(c.data); setPayloads(p.data)
        if (k.data[0]) setKeyId(String(k.data[0].id))
        if (c.data[0]) setCoverSample(c.data[0].name)
        if (p.data[0]) setPayloadSample(p.data[0].name)
      })
      .catch((e) => setError(errText(e)))
  }, [])

  const key = keys.find((k) => String(k.id) === keyId)
  const payloadSize = payloadMode === 'upload' ? payloadFile?.size : payloads.find((p) => p.name === payloadSample)?.size
  const cover = covers.find((c) => c.name === coverSample)
  // bundle = file + RSA-wrapped key + magic/nonce/tag + small header; this is an estimate shown before sending
  const estimate = payloadSize != null && key ? payloadSize + key.bits / 8 + 170 : null
  const capacity = coverMode === 'sample' ? cover?.capacity_bytes : null
  const pct = estimate != null && capacity ? (estimate / capacity) * 100 : null

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError(''); setResult(null)
    const fd = new FormData()
    fd.append('key_id', keyId)
    if (payloadMode === 'upload') fd.append('payload', payloadFile); else fd.append('payload_sample', payloadSample)
    if (coverMode === 'upload') fd.append('cover', coverFile); else fd.append('cover_sample', coverSample)
    try {
      const { data } = await api.post('/send', fd)
      setResult(data)
    } catch (err) {
      setError(errText(err))
    } finally {
      setBusy(false)
    }
  }

  const ready = keyId && (payloadMode === 'upload' ? payloadFile : payloadSample) && (coverMode === 'upload' ? coverFile : coverSample)

  return (
    <>
      <PageHead icon={SendIcon} title="Send" sub="Encrypt a file for a receiver and hide the result inside a cover image. The output is always a PNG." />
      <div className="grid gap-4 lg:grid-cols-5">
        <form onSubmit={submit} className="card space-y-4 lg:col-span-2">
          <div>
            <label className="label" htmlFor="rk">Receiver's key</label>
            <select id="rk" className="input" value={keyId} onChange={(e) => setKeyId(e.target.value)} required>
              {keys.length === 0 && <option value="">No keys - create one on the Keys page</option>}
              {keys.map((k) => <option key={k.id} value={k.id}>{k.name} ({k.bits}-bit{k.has_private ? '' : ', public only'})</option>)}
            </select>
            {keys.length === 0 && <Link to="/keys" className="mt-1 inline-block text-sm text-brand-700 hover:underline">Go to Keys</Link>}
          </div>

          <div>
            <div className="mb-1 flex items-center justify-between"><span className="label !mb-0">File to protect</span>
              <button type="button" className="text-xs text-brand-700 hover:underline" onClick={() => setPayloadMode(payloadMode === 'sample' ? 'upload' : 'sample')}>
                {payloadMode === 'sample' ? 'Upload my own' : 'Use a sample'}</button></div>
            {payloadMode === 'sample' ? (
              <select className="input" aria-label="Sample file" value={payloadSample} onChange={(e) => setPayloadSample(e.target.value)}>
                {payloads.map((p) => <option key={p.name} value={p.name}>{p.name} - {fmtBytes(p.size_bytes)}</option>)}
              </select>
            ) : (
              <input type="file" aria-label="File to protect" className="input" onChange={(e) => setPayloadFile(e.target.files[0] || null)} />
            )}
          </div>

          <div>
            <div className="mb-1 flex items-center justify-between"><span className="label !mb-0">Cover image</span>
              <button type="button" className="text-xs text-brand-700 hover:underline" onClick={() => setCoverMode(coverMode === 'sample' ? 'upload' : 'sample')}>
                {coverMode === 'sample' ? 'Upload my own' : 'Use a sample'}</button></div>
            {coverMode === 'sample' ? (
              <select className="input" aria-label="Sample cover" value={coverSample} onChange={(e) => setCoverSample(e.target.value)}>
                {covers.map((c) => <option key={c.name} value={c.name}>{c.name} - holds {fmtBytes(c.capacity_bytes)}</option>)}
              </select>
            ) : (
              <input type="file" aria-label="Cover image" accept="image/*" className="input" onChange={(e) => setCoverFile(e.target.files[0] || null)} />
            )}
          </div>

          {pct != null && (
            <div>
              <div className="mb-1 flex justify-between text-xs text-slate-500">
                <span>Capacity check (estimate)</span><span>{fmtBytes(Math.round(estimate))} of {fmtBytes(capacity)} ({pct.toFixed(1)}%)</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div className={`h-full ${pct > 100 ? 'bg-red-500' : 'bg-brand-500'}`} style={{ width: `${Math.min(pct, 100)}%` }} /></div>
              {pct > 100 && <p className="mt-1 text-xs text-red-600">Too large for this cover. Choose a bigger image or a smaller file.</p>}
            </div>
          )}

          <ErrorBox>{error}</ErrorBox>
          <button className="btn-primary w-full" disabled={busy || !ready}>
            {busy ? <Spinner text="Encrypting and embedding..." /> : 'Encrypt and hide'}
          </button>
        </form>

        <div className="card lg:col-span-3">
          {!result && <p className="text-sm text-slate-500">The stego image and its measurements appear here.</p>}
          {result && (
            <div className="space-y-4">
              <h2>Stego image ready</h2>
              <AuthImage path={`/ops/${result.op_id}/stego`} alt="Stego image" className="max-h-72 w-full rounded-lg border border-slate-200 object-contain" />
              <div className="flex flex-wrap gap-2">
                <button className="btn-primary" onClick={() => download(`/ops/${result.op_id}/stego`, `stego_${result.op_id}.png`)}><Download className="h-4 w-4" /> Download PNG</button>
                <Link className="btn-ghost" to={`/analysis?op=${result.op_id}`}>Open analysis</Link>
                <Link className="btn-ghost" to={`/receive?op=${result.op_id}`}>Try receiving it</Link>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Stat label="PSNR" value={`${result.quality.psnr_db} dB`} tone="good" hint="above 50 dB is invisible" />
                <Stat label="SSIM" value={result.quality.ssim} tone="good" hint="1 = identical" />
                <Stat label="Capacity used" value={`${result.capacity.used_pct}%`} hint={`${result.capacity.payload_bits_per_pixel} bits/pixel`} />
                <Stat label="Hidden" value={fmtBytes(result.bundle_bytes)} hint={`from ${fmtBytes(result.payload_bytes)} file`} />
              </div>
              <Timings items={[['Encrypt', fmtMs(result.timings_ms.encrypt)], ['Embed', fmtMs(result.timings_ms.embed)],
                ['PNG encode', fmtMs(result.timings_ms.png_encode)], ['Metrics', fmtMs(result.timings_ms.metrics)]]} />
              <HashLine label="SHA-256 of the file you sent" value={result.input_sha256} />
            </div>
          )}
        </div>
      </div>
    </>
  )
}

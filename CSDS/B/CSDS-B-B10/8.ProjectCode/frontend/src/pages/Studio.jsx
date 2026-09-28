import { useEffect, useState } from 'react'
import { CheckCircle2, Download, KeyRound, Lock, Unlock, XCircle } from 'lucide-react'
import api, { download, errMsg, sourceForm } from '../api'
import { ErrorBox, Figure, Histogram, KeyInput, SourcePicker, Spinner, Stat, fmt } from '../components/ui'

function flipBit(hex) {
  const first = parseInt(hex.slice(0, 2), 16) ^ 1
  return first.toString(16).padStart(2, '0') + hex.slice(2)
}

export default function Studio() {
  const [src, setSrc] = useState(null)
  const [key, setKey] = useState('')
  const [enc, setEnc] = useState(null)
  const [dec, setDec] = useState(null)
  const [decKey, setDecKey] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [jobs, setJobs] = useState([])
  const [fileDec, setFileDec] = useState({ file: null, nonce: '', key: '' })
  const [fileRes, setFileRes] = useState(null)

  const loadJobs = () => api.get('/studio/jobs').then((r) => setJobs(r.data)).catch(() => {})
  useEffect(() => { loadJobs() }, [])

  const run = async (label, fn) => {
    setBusy(label)
    setError('')
    try { await fn() } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }

  const encrypt = () => run('encrypt', async () => {
    const r = await api.post('/studio/encrypt', sourceForm(src, key))
    setEnc(r.data)
    setKey(r.data.key)
    setDecKey(r.data.key)
    setDec(null)
    loadJobs()
  })

  const decrypt = (k) => run('decrypt', async () => {
    const fd = new FormData()
    fd.append('job_id', enc.job.id)
    fd.append('key', k)
    setDecKey(k)
    setDec((await api.post('/studio/decrypt', fd)).data)
  })

  const decryptFile = () => run('file', async () => {
    const fd = new FormData()
    fd.append('file', fileDec.file)
    fd.append('nonce', fileDec.nonce)
    fd.append('key', fileDec.key)
    setFileRes((await api.post('/studio/decrypt', fd)).data)
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Image studio</h1>
        <p className="text-sm text-slate-500">Encrypt a drone image, inspect the wavelet sub-bands and the cipher, then decrypt it and verify the checksum.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="card h-fit space-y-4">
          <SourcePicker value={src} onChange={setSrc} />
          <KeyInput value={key} onChange={setKey} allowEmpty />
          <button className="btn-primary w-full" onClick={encrypt} disabled={!src || !!busy || (key && !/^[0-9a-fA-F]{64}$/.test(key))}>
            {busy === 'encrypt' ? <Spinner label="Encrypting..." /> : <><Lock className="h-4 w-4" /> Encrypt</>}
          </button>
          <ErrorBox error={error} />
        </div>

        <div className="space-y-6">
          {!enc && !busy && <div className="card text-sm text-slate-500">Pick an image and press Encrypt. Leave the key empty to generate a fresh 256-bit key.</div>}
          {busy === 'encrypt' && !enc && <div className="card"><Spinner label="Running the wavelet + chaos pipeline..." /></div>}
          {enc && (
            <>
              <div className="card space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="h2">Encryption result - {enc.job.name}</h2>
                  <button className="btn-secondary" onClick={() => download(`/studio/jobs/${enc.job.id}/cipher.png`, `cipher_${enc.job.id}_${enc.job.nonce}.png`)}>
                    <Download className="h-4 w-4" /> Cipher PNG
                  </button>
                </div>
                {enc.resized && <p className="text-xs text-amber-700">The upload was scaled to 1024 px on the long side before encryption.</p>}
                <div className="grid gap-3 sm:grid-cols-3">
                  <Figure src={enc.plain} caption="Original" pixel={false} />
                  <Figure src={enc.coefficients} caption="Integer Haar DWT coefficients (LL | HL / LH | HH)" />
                  <Figure src={enc.cipher} caption="Cipher image" />
                </div>
                <div className="grid gap-3 sm:grid-cols-4">
                  <Stat label="Size" value={`${enc.job.width}×${enc.job.height}`} sub={`${enc.job.channels} channel(s)`} />
                  <Stat label="Encryption" value={`${fmt(enc.job.enc_ms, 1)} ms`} sub={`+ ${fmt(enc.key_setup_ms, 0)} ms one-off key setup`} />
                  <Stat label="Key fingerprint" value={<span className="font-mono text-base">{enc.job.key_fp}</span>} />
                  <Stat label="Nonce" value={<span className="break-all font-mono text-xs">{enc.job.nonce}</span>} />
                </div>
                <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800">
                  <KeyRound className="mr-1 inline h-3.5 w-3.5" /> Key (keep it secret - it is not stored on the server):
                  <div className="mt-1 break-all font-mono">{enc.key}</div>
                </div>
                <div className="text-xs text-slate-500">Original SHA-256: <span className="font-mono">{enc.job.plain_sha256}</span></div>
              </div>

              <div className="card">
                <h2 className="h2 mb-3">Wavelet sub-bands (PyWavelets Haar, luminance)</h2>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {['LL', 'LH', 'HL', 'HH'].map((b) => <Figure key={b} src={enc.subbands[b]} caption={b === 'LL' ? 'LL - approximation' : `${b} - detail`} />)}
                </div>
              </div>

              <div className="card grid gap-4 sm:grid-cols-2">
                <Histogram data={enc.histograms.plain} title="Histogram - original" />
                <Histogram data={enc.histograms.cipher} title="Histogram - cipher (flat = good)" />
              </div>

              <div className="card space-y-3">
                <h2 className="h2">Decrypt</h2>
                <KeyInput value={decKey} onChange={setDecKey} label="Decryption key" />
                <div className="flex flex-wrap gap-2">
                  <button className="btn-primary" onClick={() => decrypt(decKey)} disabled={!!busy || !/^[0-9a-fA-F]{64}$/.test(decKey)}>
                    {busy === 'decrypt' ? <Spinner label="Decrypting..." /> : <><Unlock className="h-4 w-4" /> Decrypt</>}
                  </button>
                  <button className="btn-secondary" onClick={() => decrypt(flipBit(enc.key))} disabled={!!busy}>
                    Try a key with 1 bit flipped
                  </button>
                  <button className="btn-secondary" onClick={() => decrypt(enc.key)} disabled={!!busy}>Use the original key</button>
                </div>
                {dec && (
                  <div className="grid gap-4 sm:grid-cols-[1fr_1fr]">
                    <Figure src={dec.decrypted} caption={`Decrypted in ${fmt(dec.dec_ms, 1)} ms`} pixel={false} />
                    <div className="space-y-3">
                      <div className={`flex items-center gap-2 rounded-lg p-3 text-sm font-medium ${dec.match ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
                        {dec.match ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                        {dec.match ? 'Checksum matches - image recovered bit-for-bit' : 'Checksum does not match - wrong key'}
                      </div>
                      <div className="text-xs text-slate-500">Decrypted SHA-256: <span className="break-all font-mono">{dec.sha256}</span></div>
                      <Histogram data={dec.histogram} title="Histogram - decrypted" />
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          <div className="card space-y-3">
            <h2 className="h2">Decrypt a cipher file</h2>
            <p className="text-xs text-slate-500">Upload a cipher PNG downloaded earlier, with its nonce (in the file name) and the key.</p>
            <div className="grid gap-3 sm:grid-cols-3">
              <input type="file" accept="image/png" className="input" onChange={(e) => {
                const f = e.target.files[0]
                const m = f?.name.match(/_([0-9a-f]{32})\.png$/)
                setFileDec({ ...fileDec, file: f, nonce: m ? m[1] : fileDec.nonce })
              }} />
              <input className="input font-mono text-xs" placeholder="nonce (32 hex)" value={fileDec.nonce} onChange={(e) => setFileDec({ ...fileDec, nonce: e.target.value.trim() })} />
              <input className="input font-mono text-xs" placeholder="key (64 hex)" value={fileDec.key} onChange={(e) => setFileDec({ ...fileDec, key: e.target.value.trim() })} />
            </div>
            <button className="btn-secondary" onClick={decryptFile} disabled={!fileDec.file || !fileDec.nonce || !fileDec.key || !!busy}>
              {busy === 'file' ? <Spinner label="Decrypting..." /> : 'Decrypt file'}
            </button>
            {fileRes && (
              <div className="grid gap-3 sm:grid-cols-2">
                <Figure src={fileRes.decrypted} caption={`Decrypted in ${fmt(fileRes.dec_ms, 1)} ms`} pixel={false} />
                <div className="text-xs text-slate-500">SHA-256 of the result: <span className="break-all font-mono">{fileRes.sha256}</span>
                  <p className="mt-2">Compare it with the original checksum in the job list below.</p></div>
              </div>
            )}
          </div>

          <div className="card">
            <h2 className="h2 mb-3">Recent encryptions</h2>
            {jobs.length === 0 ? <p className="text-sm text-slate-500">No encryptions yet.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">#</th><th>Image</th><th>Size</th><th>Enc ms</th><th>Key fp</th><th>Original SHA-256</th><th /></tr></thead>
                  <tbody>
                    {jobs.map((j) => (
                      <tr key={j.id} className="border-t border-slate-100">
                        <td className="py-2">{j.id}</td><td className="max-w-[180px] truncate">{j.name}</td><td>{j.width}×{j.height}</td>
                        <td>{fmt(j.enc_ms, 1)}</td><td className="font-mono text-xs">{j.key_fp}</td>
                        <td className="font-mono text-xs">{j.plain_sha256.slice(0, 16)}…</td>
                        <td><button className="text-sky-600 hover:underline" onClick={() => download(`/studio/jobs/${j.id}/cipher.png`, `cipher_${j.id}_${j.nonce}.png`)}>cipher</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

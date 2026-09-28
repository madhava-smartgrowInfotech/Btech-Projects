import { useEffect, useState } from 'react'
import { Gauge } from 'lucide-react'
import api, { errMsg } from '../api'
import { Bars, ErrorBox, Spinner, fmt } from '../components/ui'

function Result({ run }) {
  return (
    <div className="card space-y-5">
      <div>
        <h2 className="h2">Run #{run.id} - {run.images} image(s) at {run.size}×{run.size} RGB</h2>
        <p className="text-xs text-slate-500">{new Date(/Z|[+-]\d\d:\d\d$/.test(run.created_at) ? run.created_at : run.created_at + 'Z').toLocaleString()} · median of {run.repeats} repeat(s) per image · {(run.bytes_per_image / 1024).toFixed(0)} KB per image · {run.cpu} CPU threads</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr><th className="py-1">Algorithm</th><th>Encrypt ms</th><th>Decrypt ms</th><th>Enc MB/s</th><th>Dec MB/s</th><th>Frames/s (enc+dec)</th><th>Cipher entropy</th><th>|Corr. H|</th><th>Lossless</th></tr>
          </thead>
          <tbody>{run.results.map((r) => (
            <tr key={r.algorithm} className={`border-t border-slate-100 ${r.algorithm === 'SkyCipher' ? 'font-medium' : ''}`}>
              <td className="py-1.5">{r.algorithm}</td><td>{fmt(r.enc_ms, 2)}</td><td>{fmt(r.dec_ms, 2)}</td>
              <td>{fmt(r.enc_mbps, 1)}</td><td>{fmt(r.dec_mbps, 1)}</td><td>{fmt(r.fps_capacity, 1)}</td>
              <td>{fmt(r.cipher_entropy, 4)}</td><td>{fmt(r.cipher_corr_h, 4)}</td><td>{r.lossless ? 'yes' : 'no'}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <Bars rows={run.results} valueKey="enc_ms" label="Encryption time per image (lower is faster)" unit="ms" />
        <Bars rows={run.results} valueKey="dec_ms" label="Decryption time per image" unit="ms" />
      </div>
      <p className="text-xs text-slate-500">AES-256-CTR and ChaCha20 run as optimised native code (OpenSSL via the cryptography package) and treat the image as a byte stream. SkyCipher runs in NumPy and adds the wavelet transform, permutation and image-aware diffusion; the frames/s column shows whether it keeps up with a live video link.</p>
    </div>
  )
}

export default function Benchmark() {
  const [cfg, setCfg] = useState({ size: 512, images: 5, repeats: 3 })
  const [runs, setRuns] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { api.get('/bench/runs').then((r) => setRuns(r.data)).catch((e) => setError(errMsg(e))).finally(() => setLoading(false)) }, [])

  const run = async () => {
    setBusy(true); setError('')
    try {
      const r = await api.post('/bench/run', cfg)
      setRuns([r.data, ...runs])
    } catch (e) { setError(errMsg(e)) } finally { setBusy(false) }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Benchmark</h1>
        <p className="text-sm text-slate-500">Encryption and decryption time of SkyCipher against AES-256-CTR and ChaCha20 on the same drone images.</p>
      </div>
      <div className="card flex flex-wrap items-end gap-4">
        <div><label className="label">Image size</label>
          <select className="input" value={cfg.size} onChange={(e) => setCfg({ ...cfg, size: Number(e.target.value) })}>
            {[256, 512, 1024].map((s) => <option key={s} value={s}>{s}×{s}</option>)}
          </select></div>
        <div><label className="label">Images</label><input type="number" min="1" max="20" className="input w-24" value={cfg.images} onChange={(e) => setCfg({ ...cfg, images: Number(e.target.value) })} /></div>
        <div><label className="label">Repeats</label><input type="number" min="1" max="10" className="input w-24" value={cfg.repeats} onChange={(e) => setCfg({ ...cfg, repeats: Number(e.target.value) })} /></div>
        <button className="btn-primary" onClick={run} disabled={busy}>{busy ? <Spinner label="Benchmarking..." /> : <><Gauge className="h-4 w-4" /> Run benchmark</>}</button>
        <div className="w-full"><ErrorBox error={error} /></div>
      </div>
      {loading && <Spinner label="Loading previous runs..." />}
      {!loading && runs.length === 0 && !busy && <div className="card text-sm text-slate-500">No benchmark runs yet.</div>}
      {runs.map((r) => <Result key={r.id} run={r} />)}
    </div>
  )
}

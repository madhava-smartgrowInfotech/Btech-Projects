import { useEffect, useState } from 'react'
import { FileDown, FileJson, ShieldCheck, Zap } from 'lucide-react'
import api, { download, errMsg, sourceForm } from '../api'
import { ErrorBox, Figure, Histogram, KeyInput, Scatter, SourcePicker, Spinner, Stat, fmt } from '../components/ui'

function Metrics({ r }) {
  const cor = r.correlation
  const dirs = ['horizontal', 'vertical', 'diagonal']
  const dq = r.quality.decrypted
  return (
    <>
      <div className="card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="h2">Report #{r.id} - {r.image_name}</h2>
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => download(`/lab/reports/${r.id}/export?fmt=html`, `skycipher_report_${r.id}.html`)}><FileDown className="h-4 w-4" /> HTML report</button>
            <button className="btn-secondary" onClick={() => download(`/lab/reports/${r.id}/export?fmt=json`, `skycipher_report_${r.id}.json`)}><FileJson className="h-4 w-4" /> JSON</button>
          </div>
        </div>
        {r.thumbs && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Figure src={r.thumbs.plain} caption="Original" pixel={false} />
            <Figure src={r.thumbs.cipher} caption="Cipher" />
            <Figure src={r.thumbs.decrypted} caption="Decrypted (right key)" pixel={false} />
            <Figure src={r.thumbs.wrong_key} caption="Decrypted with 1 key bit flipped" />
          </div>
        )}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Stat label="Entropy (cipher)" value={fmt(r.entropy.cipher.mean)} sub={`ideal 8 · original ${fmt(r.entropy.plain.mean)}`} good={r.entropy.cipher.mean > 7.99} />
          <Stat label="NPCR" value={`${fmt(r.differential.npcr, 3)}%`} sub={`ideal ${r.differential.ideal_npcr}%`} good={r.differential.npcr > 99.5} />
          <Stat label="UACI" value={`${fmt(r.differential.uaci, 3)}%`} sub={`ideal ${r.differential.ideal_uaci}%`} good={Math.abs(r.differential.uaci - 33.46) < 0.6} />
          <Stat label="Histogram χ²" value={r.chi_square.cipher.per_channel.map((v) => v.toFixed(0)).join(' / ')} sub={`uniform if < ${r.chi_square.cipher.critical.toFixed(1)}`} good={r.chi_square.cipher.uniform} />
          <Stat label="Decrypted PSNR" value={dq.psnr === 'inf' ? '∞ dB' : `${fmt(dq.psnr, 2)} dB`} sub={`MSE ${fmt(dq.mse, 2)} · SSIM ${fmt(dq.ssim, 3)}`} good={dq.identical} />
          <Stat label="Cipher vs original" value={`${fmt(r.quality.cipher_vs_plain.psnr, 2)} dB`} sub={`MSE ${fmt(r.quality.cipher_vs_plain.mse, 0)} · SSIM ${fmt(r.quality.cipher_vs_plain.ssim, 3)}`} />
          <Stat label="Key space" value={`2^${r.key_space.key_bits}`} sub={`+ ${r.key_space.nonce_bits}-bit public nonce`} good />
          <Stat label="Timing" value={`${fmt(r.timing.encrypt_ms, 1)} / ${fmt(r.timing.decrypt_ms, 1)} ms`} sub={`enc / dec · ${fmt(r.timing.throughput_mbps, 2)} MB/s${r.timing.key_setup_ms !== undefined ? ` · key setup ${fmt(r.timing.key_setup_ms, 0)} ms` : ''}`} />
        </div>
        <div className={`rounded-lg p-3 text-sm ${dq.identical ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
          {dq.identical ? 'Decryption is bit-identical to the original (SHA-256 match).' : 'Decryption did not reproduce the original.'}
        </div>
      </div>

      <div className="card space-y-4">
        <h2 className="h2">Correlation of adjacent pixels</h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500"><tr><th className="py-1">Direction</th><th>Original</th><th>Cipher</th></tr></thead>
          <tbody>{dirs.map((d) => (
            <tr key={d} className="border-t border-slate-100"><td className="py-1.5 capitalize">{d}</td><td>{fmt(cor.plain[d])}</td><td className="font-semibold">{fmt(cor.cipher[d])}</td></tr>
          ))}</tbody>
        </table>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-6">
          {dirs.map((d) => <Scatter key={`p${d}`} points={cor.plain.scatter?.[d]} title={`Original - ${d}`} />)}
          {dirs.map((d) => <Scatter key={`c${d}`} points={cor.cipher.scatter?.[d]} title={`Cipher - ${d}`} />)}
        </div>
      </div>

      <div className="card grid gap-4 sm:grid-cols-2">
        <Histogram data={r.histograms.plain} title="Histogram - original" />
        <Histogram data={r.histograms.cipher} title="Histogram - cipher" />
      </div>

      <div className="card">
        <h2 className="h2 mb-2">Key sensitivity</h2>
        <p className="mb-3 text-sm text-slate-500">One key bit flipped at a time: the cipher changes almost completely and the wrong key recovers nothing.</p>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500"><tr><th className="py-1">Flipped bit</th><th>Cipher NPCR</th><th>Cipher UACI</th><th>Wrong-key decrypt PSNR</th><th>Pixels differing</th></tr></thead>
          <tbody>{r.key_sensitivity.tests.map((t) => (
            <tr key={t.bit} className="border-t border-slate-100">
              <td className="py-1.5">{t.bit}</td><td>{fmt(t.cipher_diff.npcr, 3)}%</td><td>{fmt(t.cipher_diff.uaci, 3)}%</td>
              <td>{fmt(t.wrong_key_decrypt.psnr, 2)} dB</td><td>{fmt(t.wrong_key_decrypt.npcr, 2)}%</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </>
  )
}

function Attacks({ data }) {
  return (
    <div className="card space-y-4">
      <h2 className="h2">Attack tests - {data.image_name}</h2>
      <p className="text-sm text-slate-500">The cipher image is damaged in transit, then decrypted with the right key. Chained diffusion keeps damage local to a few coefficients, so impulse noise and cropping leave most of the image readable; dense noise that touches every byte does not recover.</p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500"><tr><th className="py-1">Attack</th><th>Cipher bytes changed</th><th>Recovered PSNR</th><th>SSIM</th><th>Pixels intact</th><th>After 3×3 median</th></tr></thead>
          <tbody>{data.results.map((a) => (
            <tr key={a.label} className="border-t border-slate-100">
              <td className="py-1.5">{a.label}</td><td>{fmt(a.cipher_bytes_changed_pct, 2)}%</td><td>{fmt(a.recovered.psnr, 2)} dB</td>
              <td>{fmt(a.recovered.ssim, 3)}</td><td className="font-semibold">{fmt(a.recovered.intact_pct, 1)}%</td><td>{fmt(a.median_filtered.psnr, 2)} dB</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <div className="space-y-4">
        {data.results.map((a) => (
          <div key={a.label}>
            <div className="mb-1 text-sm font-medium text-slate-700">{a.label}</div>
            <div className="grid grid-cols-3 gap-3">
              <Figure src={a.attacked_preview} caption="Damaged cipher" />
              <Figure src={a.recovered_preview} caption={`Recovered · ${fmt(a.recovered.intact_pct, 1)}% intact`} pixel={false} />
              <Figure src={a.filtered_preview} caption="Recovered + median filter" pixel={false} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Lab() {
  const [src, setSrc] = useState(null)
  const [key, setKey] = useState('')
  const [report, setReport] = useState(null)
  const [attacks, setAttacks] = useState(null)
  const [reports, setReports] = useState([])
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')

  const loadReports = () => api.get('/lab/reports').then((r) => setReports(r.data)).catch(() => {})
  useEffect(() => { loadReports() }, [])

  const run = async (label, fn) => {
    setBusy(label)
    setError('')
    try { await fn() } catch (e) { setError(errMsg(e)) } finally { setBusy('') }
  }
  const analyze = () => run('analyze', async () => {
    setAttacks(null)
    setReport((await api.post('/lab/analyze', sourceForm(src, key))).data)
    loadReports()
  })
  const attack = () => run('attack', async () => {
    const fd = sourceForm(src, key)
    if (report) fd.append('report_id', report.id)
    setAttacks((await api.post('/attacks/run', fd)).data)
    loadReports()
  })
  const open = (id) => run('open', async () => {
    setAttacks(null)
    setReport((await api.get(`/lab/reports/${id}`)).data)
  })
  const keyOk = !key || /^[0-9a-fA-F]{64}$/.test(key)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Security lab</h1>
        <p className="text-sm text-slate-500">Statistical, differential and key-sensitivity analysis, plus channel-damage tests. Every run is saved as an exportable report.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4">
          <div className="card space-y-4">
            <SourcePicker value={src} onChange={setSrc} />
            <KeyInput value={key} onChange={setKey} allowEmpty />
            <button className="btn-primary w-full" onClick={analyze} disabled={!src || !!busy || !keyOk}>
              {busy === 'analyze' ? <Spinner label="Analysing..." /> : <><ShieldCheck className="h-4 w-4" /> Run security analysis</>}
            </button>
            <button className="btn-secondary w-full" onClick={attack} disabled={!src || !!busy || !keyOk}>
              {busy === 'attack' ? <Spinner label="Attacking..." /> : <><Zap className="h-4 w-4" /> Run attack tests</>}
            </button>
            {report && <p className="text-xs text-slate-500">Attack results are added to report #{report.id}.</p>}
            <ErrorBox error={error} />
          </div>
          <div className="card">
            <h2 className="h2 mb-2">Saved reports</h2>
            {reports.length === 0 ? <p className="text-sm text-slate-500">No reports yet.</p> : (
              <ul className="divide-y divide-slate-100 text-sm">
                {reports.map((r) => (
                  <li key={r.id}>
                    <button className="w-full py-2 text-left hover:text-sky-700" onClick={() => open(r.id)}>
                      <div className="truncate font-medium">#{r.id} {r.image_name}</div>
                      <div className="text-xs text-slate-500">NPCR {fmt(r.npcr, 2)}% · UACI {fmt(r.uaci, 2)}% · H {fmt(r.entropy, 4)}{r.has_attacks ? ' · attacks' : ''}</div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        <div className="space-y-6">
          {!report && !attacks && !busy && <div className="card text-sm text-slate-500">Choose an image and run the security analysis or the attack tests.</div>}
          {(busy === 'analyze' || busy === 'open') && <div className="card"><Spinner label="Encrypting and measuring... (a few seconds for large images)" /></div>}
          {busy === 'attack' && <div className="card"><Spinner label="Damaging the cipher image and decrypting..." /></div>}
          {attacks && <Attacks data={attacks} />}
          {report && <Metrics r={report} />}
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Gauge, ShieldHalf } from 'lucide-react'
import api, { errText, fmtBytes, fmtMs } from '../api'
import SendPicker from '../components/SendPicker'
import { Badge, ErrorBox, PageHead, Spinner } from '../components/ui'

export default function Robustness() {
  const [op, setOp] = useState(null)
  const [report, setReport] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [capacity, setCapacity] = useState(null)
  const [bench, setBench] = useState(null)
  const [benchBusy, setBenchBusy] = useState(false)

  useEffect(() => {
    api.get('/benchmark/capacity').then((r) => setCapacity(r.data)).catch((e) => setError(errText(e)))
  }, [])

  useEffect(() => {
    setReport(null)
    if (op) api.get(`/robustness/${op.id}`).then((r) => setReport(r.data)).catch(() => {})
  }, [op?.id])

  async function runAttacks() {
    setBusy(true); setError('')
    try { setReport((await api.post(`/robustness/${op.id}`)).data) } catch (e) { setError(errText(e)) } finally { setBusy(false) }
  }
  async function runBench() {
    setBenchBusy(true); setError('')
    try { setBench((await api.post('/benchmark/run')).data) } catch (e) { setError(errText(e)) } finally { setBenchBusy(false) }
  }

  const jpegLost = report?.results.some((r) => r.attack.startsWith('jpeg') && r.status !== 'recovered')

  return (
    <>
      <PageHead icon={ShieldHalf} title="Robustness and benchmark"
        sub="LSB hiding survives lossless handling and nothing else. This page attacks a stego image and states exactly what lives and what dies, then measures capacity and speed across covers." />
      <div className="mb-4"><ErrorBox>{error}</ErrorBox></div>

      <div className="card mb-6 space-y-4">
        <h2>Attack a stego image</h2>
        <SendPicker onChange={setOp} />
        <button className="btn-primary" disabled={!op || busy} onClick={runAttacks}>
          {busy ? <Spinner text="Recompressing, adding noise, cropping..." /> : 'Run robustness tests'}
        </button>

        {report && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-slate-200"><tr>
                  <th className="th">Attack</th><th className="th">Result</th><th className="th">LSB error rate</th><th className="th">What happened</th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {report.results.map((r) => (
                    <tr key={r.attack} className="align-top">
                      <td className="td font-medium">{r.label}<div className="text-xs font-normal text-slate-400">{r.size}</div></td>
                      <td className="td"><Badge tone={r.status === 'recovered' ? 'good' : 'bad'}>{r.status === 'recovered' ? 'payload survives' : 'payload lost'}</Badge></td>
                      <td className="td font-mono text-xs">{r.bit_error_rate == null ? '-' : `${(r.bit_error_rate * 100).toFixed(1)}%`}</td>
                      <td className="td text-slate-600">{r.why}<div className="mt-0.5 text-xs text-slate-400">{r.detail}</div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
              <b>Survives:</b> {report.survived.join(', ') || 'nothing'}. <b>Lost:</b> {report.lost.join(', ') || 'nothing'}.
              {jpegLost && ' JPEG recompression rewrites the lowest bits of every pixel, so the hidden bundle cannot be read back. Always send and store the stego image as PNG, and avoid chat apps or sites that re-encode pictures.'}
            </div>
          </>
        )}
      </div>

      <div className="card mb-6">
        <h2 className="mb-3">Capacity per cover</h2>
        {!capacity ? <Spinner text="Loading..." /> : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-200"><tr>
                <th className="th">Cover</th><th className="th">Size (px)</th><th className="th">Maximum hidden</th><th className="th">Bits / pixel</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {capacity.map((c) => (
                  <tr key={c.cover}><td className="td font-medium">{c.cover}</td><td className="td">{c.width} x {c.height}</td>
                    <td className="td">{fmtBytes(c.max_bundle_bytes)}</td><td className="td">{c.max_bits_per_pixel}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card space-y-3">
        <h2 className="flex items-center gap-2"><Gauge className="h-5 w-5" /> Speed and quality benchmark</h2>
        <p className="text-sm text-slate-500">Runs the full encrypt, embed, extract, decrypt cycle on every sample cover at 1 KiB, 16 KiB and 64 KiB payloads (RSA-2048 key, median of 2 runs).</p>
        <button className="btn-primary" disabled={benchBusy} onClick={runBench}>{benchBusy ? <Spinner text="Benchmarking..." /> : 'Run benchmark'}</button>
        {bench && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-200"><tr>
                {['Cover', 'Payload', 'Used', 'PSNR', 'SSIM', 'Encrypt', 'Embed', 'Extract', 'Decrypt'].map((h) => <th key={h} className="th">{h}</th>)}
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {bench.rows.map((r, i) => r.fits ? (
                  <tr key={i}><td className="td">{r.cover}</td><td className="td">{fmtBytes(r.payload_bytes)}</td><td className="td">{r.used_pct}%</td>
                    <td className="td">{r.psnr_db} dB</td><td className="td">{r.ssim}</td><td className="td">{fmtMs(r.encrypt_ms)}</td>
                    <td className="td">{fmtMs(r.embed_ms)}</td><td className="td">{fmtMs(r.extract_ms)}</td><td className="td">{fmtMs(r.decrypt_ms)}</td></tr>
                ) : (
                  <tr key={i} className="text-slate-400"><td className="td">{r.cover}</td><td className="td">{fmtBytes(r.payload_bytes)}</td>
                    <td className="td" colSpan={7}>does not fit - blocked by the capacity check</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}

import { useState } from 'react'
import { FileSearch } from 'lucide-react'
import SendPicker from '../components/SendPicker'
import { AuthImage, PageHead, Stat, Timings } from '../components/ui'
import { fmtBytes, fmtMs } from '../api'

export default function Analysis() {
  const [op, setOp] = useState(null)
  const d = op?.details
  const psnrOk = d && (d.quality.psnr_db == null || d.quality.psnr_db > 50)

  return (
    <>
      <PageHead icon={FileSearch} title="Analysis"
        sub="How visible is the hidden data? PSNR and SSIM compare the stego image with the original cover; the histograms and bit planes show where the change lives." />
      <div className="card mb-4"><SendPicker onChange={setOp} /></div>

      {d && (
        <div className="space-y-4">
          <div className="card">
            <h2 className="mb-3">Imperceptibility</h2>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
              <Stat label="PSNR" value={`${d.quality.psnr_db ?? 'inf'} dB`} tone={psnrOk ? 'good' : 'bad'} hint="> 50 dB is invisible" />
              <Stat label="SSIM" value={d.quality.ssim} tone="good" hint="1 = identical" />
              <Stat label="MSE" value={d.quality.mse} />
              <Stat label="Largest change" value={`${d.quality.max_abs_change} / 255`} hint="per colour value" />
              <Stat label="Values changed" value={`${d.quality.changed_pct}%`} hint={`${d.quality.values_changed.toLocaleString()} of ${d.quality.values_total.toLocaleString()}`} />
              <Stat label="Capacity used" value={`${d.capacity.used_pct}%`} hint={`${d.capacity.payload_bits_per_pixel} bits/pixel`} />
            </div>
          </div>

          <div className="card">
            <h2 className="mb-3">Cover and stego, side by side</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {[['Original cover', 'cover'], ['Stego image', 'stego']].map(([t, w]) => (
                <figure key={w}>
                  <AuthImage path={`/ops/${op.id}/${w}`} alt={t} className="max-h-80 w-full rounded-lg border border-slate-200 object-contain" />
                  <figcaption className="mt-1 text-center text-xs text-slate-500">{t}</figcaption>
                </figure>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-500">Cover {d.capacity.width} x {d.capacity.height} px, holds up to {fmtBytes(d.capacity.max_bundle_bytes)}; this message used {fmtBytes(d.capacity.bundle_bytes)}.</p>
          </div>

          <div className="card">
            <h2 className="mb-3">Histograms</h2>
            <AuthImage path={`/analysis/${op.id}/histogram.png`} alt="Histograms of cover and stego" className="w-full" />
            <p className="mt-2 text-xs text-slate-500">Grey is the cover, the coloured line is the stego image. Changing only the lowest bit moves counts between neighbouring values, so the overall shape stays the same.</p>
          </div>

          <div className="card">
            <h2 className="mb-3">Bit planes</h2>
            <AuthImage path={`/analysis/${op.id}/bitplanes.png`} alt="Bit planes of cover and stego" className="mx-auto w-full max-w-3xl" />
            <p className="mt-2 text-xs text-slate-500">Plane 0 (least significant) is where the data goes: the stego version looks like noise in the rows that carry data. Higher planes, which make up the picture you see, are identical.</p>
          </div>

          <div className="card">
            <h2 className="mb-3">Processing time for this message</h2>
            <Timings items={[['Encrypt (AES + RSA)', fmtMs(d.timings_ms.encrypt)], ['LSB embed', fmtMs(d.timings_ms.embed)],
              ['PNG encode', fmtMs(d.timings_ms.png_encode)], ['PSNR + SSIM', fmtMs(d.timings_ms.metrics)]]} />
          </div>
        </div>
      )}
    </>
  )
}

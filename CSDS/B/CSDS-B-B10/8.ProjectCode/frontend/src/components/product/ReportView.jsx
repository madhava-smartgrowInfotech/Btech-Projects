import { Badge, Card, KeyValueList, StatCard } from '../ui/display'
import Table from '../ui/Table'
import { db, num, pct, when } from '../../format'
import ImagePanel from './ImagePanel'
import { CorrelationScatter, HistogramChart } from './charts'

const DIRS = ['horizontal', 'vertical', 'diagonal']

// One security analysis. Used for a fresh analysis and for a saved report (both return the same shape).
export default function ReportView({ report }) {
  const { id, created_at, image, image_name, key_fp, nonce, entropy, chi_square, correlation, differential,
    quality, key_sensitivity, key_space, timing, histograms, thumbs, attacks } = report
  const worst = Math.max(...DIRS.map((d) => Math.abs(correlation.cipher[d])))
  const dec = quality.decrypted

  return (
    <div className="space-y-5">
      <Card title={`Report ${id ? `#${id}` : ''}`.trim()} eyebrow={when(created_at)}>
        <KeyValueList cols={2} items={[
          ['Image', image_name],
          ['Size', `${image.width} × ${image.height}, ${image.channels} channel${image.channels > 1 ? 's' : ''}`],
          ['Key fingerprint', <code key="fp" className="break-all">{key_fp}</code>],
          ['Nonce', <code key="n" className="break-all">{nonce}</code>],
        ]} />
      </Card>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Entropy (cipher)" value={entropy.cipher.mean} format={(v) => num(v, 4)}
          sub={`ideal 8 · original ${num(entropy.plain.mean, 3)}`} tone="ok" />
        <StatCard label="NPCR" value={differential.npcr} format={(v) => pct(v, 2)}
          sub={`ideal ${differential.ideal_npcr}%`} tone="ok" />
        <StatCard label="UACI" value={differential.uaci} format={(v) => pct(v, 2)}
          sub={`ideal ${differential.ideal_uaci}%`} tone="ok" />
        <StatCard label="Max |correlation|" value={worst} format={(v) => num(v, 4)}
          sub="ideal 0 · cipher, adjacent pixels" tone="cyan" />
      </div>

      {thumbs && (
        <Card title="Images">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <ImagePanel src={thumbs.plain} caption="Original" />
            <ImagePanel src={thumbs.cipher} caption="Cipher" />
            <ImagePanel src={thumbs.decrypted} caption="Decrypted" />
            <ImagePanel src={thumbs.wrong_key} caption="Wrong key (1 bit)" />
          </div>
        </Card>
      )}

      <Card title="Statistical analysis" bodyClass="p-0">
        <Table
          rowKey={(r) => r.metric}
          columns={[
            { key: 'metric', label: 'Metric' },
            { key: 'cipher', label: 'Cipher', align: 'right' },
            { key: 'plain', label: 'Original', align: 'right' },
          ]}
          rows={[
            { metric: 'Entropy, bits (ideal 8)', cipher: num(entropy.cipher.mean, 4), plain: num(entropy.plain.mean, 4) },
            { metric: `Chi-square per channel (uniform < ${chi_square.cipher.critical})`,
              cipher: chi_square.cipher.per_channel.map((v) => num(v, 1)).join(' · '),
              plain: chi_square.plain.per_channel.map((v) => num(v, 0)).join(' · ') },
            ...DIRS.map((d) => ({ metric: `Correlation ${d} (ideal 0)`, cipher: num(correlation.cipher[d], 4), plain: num(correlation.plain[d], 4) })),
          ]}
        />
        <p className="mt-3 font-mono text-[11px] text-dim">
          Histogram test: cipher is {chi_square.cipher.uniform ? 'uniform on every channel' : 'not uniform on every channel'} at alpha = 0.05.
        </p>
      </Card>

      {histograms && (
        <Card title="Histograms">
          <div className="grid gap-5 md:grid-cols-2">
            <div><div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-dim">Original</div><HistogramChart hist={histograms.plain} label="Original histogram" /></div>
            <div><div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-dim">Cipher</div><HistogramChart hist={histograms.cipher} label="Cipher histogram" /></div>
          </div>
        </Card>
      )}

      {correlation.plain.scatter && (
        <Card title="Correlation of adjacent pixels">
          <CorrelationScatter plain={correlation.plain.scatter.horizontal} cipher={correlation.cipher.scatter.horizontal}
            label="Horizontal neighbour pairs, original and cipher" />
          <p className="mt-2 font-mono text-[11px] text-dim">Horizontal pairs. A flat cloud means no visible structure.</p>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Differential attack and quality">
          <KeyValueList items={[
            ['NPCR, 1-pixel change', `${pct(differential.npcr)} (ideal ${differential.ideal_npcr}%)`],
            ['UACI, 1-pixel change', `${pct(differential.uaci)} (ideal ${differential.ideal_uaci}%)`],
            ['Decrypted vs original', <Badge key="id" tone={dec.identical ? 'ok' : 'alert'}>{dec.identical ? 'bit-identical' : 'not identical'}</Badge>],
            ['Decrypted PSNR / SSIM', `${db(dec.psnr)} · ${num(dec.ssim, 4)}`],
            ['Cipher PSNR / SSIM', `${db(quality.cipher_vs_plain.psnr)} · ${num(quality.cipher_vs_plain.ssim, 4)}`],
          ]} />
        </Card>
        <Card title="Key space and timing">
          <KeyValueList items={[
            ['Key space', `2^${key_space.key_bits} (+ ${key_space.nonce_bits}-bit public nonce)`],
            ['Key setup (once per key)', `${num(timing.key_setup_ms, 1)} ms`],
            ['Encrypt / decrypt', `${num(timing.encrypt_ms, 1)} ms · ${num(timing.decrypt_ms, 1)} ms`],
            ['Throughput', `${num(timing.throughput_mbps, 2)} MB/s`],
          ]} />
        </Card>
      </div>

      <Card title="Key sensitivity (single-bit key changes)" bodyClass="p-0">
        <Table
          rowKey={(t) => t.bit}
          columns={[
            { key: 'bit', label: 'Flipped bit' },
            { key: 'npcr', label: 'Cipher NPCR', align: 'right', render: (t) => pct(t.cipher_diff.npcr) },
            { key: 'uaci', label: 'Cipher UACI', align: 'right', render: (t) => pct(t.cipher_diff.uaci) },
            { key: 'psnr', label: 'Wrong-key PSNR', align: 'right', render: (t) => db(t.wrong_key_decrypt.psnr) },
          ]}
          rows={key_sensitivity.tests}
        />
        <p className="px-4 pb-4 pt-3 font-mono text-[11px] text-dim">
          Lowest cipher NPCR {pct(key_sensitivity.min_cipher_npcr)} (ideal ~99.6%).
          {key_sensitivity.wrong_key_recovers ? ' A wrong key recovered part of the image.' : ' No wrong key recovered the image.'}
        </p>
      </Card>

      {attacks && (
        <Card title="Attack tests (cipher damaged, then decrypted)" bodyClass="p-0">
          <Table
            rowKey={(a) => a.label}
            columns={[
              { key: 'label', label: 'Attack' },
              { key: 'psnr', label: 'Recovered PSNR', align: 'right', render: (a) => db(a.recovered.psnr) },
              { key: 'ssim', label: 'SSIM', align: 'right', render: (a) => num(a.recovered.ssim, 3) },
              { key: 'intact', label: 'Pixels intact', align: 'right', render: (a) => pct(a.recovered.intact_pct) },
              { key: 'median', label: 'After 3x3 median', align: 'right', render: (a) => db(a.median_filtered.psnr) },
            ]}
            rows={attacks}
          />
        </Card>
      )}
    </div>
  )
}

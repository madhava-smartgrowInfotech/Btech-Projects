import { Gauge, Play } from 'lucide-react'
import { useEffect, useState } from 'react'
import api, { describeError } from '../api'
import { BenchChart } from '../components/product/charts'
import { PageHeader } from '../components/ui/AppShell'
import { Button, Select, Input } from '../components/ui/controls'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import Table from '../components/ui/Table'
import { num, when } from '../format'

const SIZES = [256, 512, 1024]

export default function Benchmark() {
  const toast = useToast()
  const [size, setSize] = useState(512)
  const [images, setImages] = useState(5)
  const [repeats, setRepeats] = useState(3)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [runs, setRuns] = useState(null)
  const [runsError, setRunsError] = useState(null)

  const imagesOk = Number(images) >= 1 && Number(images) <= 20
  const repeatsOk = Number(repeats) >= 1 && Number(repeats) <= 10
  const canRun = imagesOk && repeatsOk && !busy

  function loadRuns() {
    return api.get('/bench/runs')
      .then((r) => { setRuns(r.data); setRunsError(null) })
      .catch((e) => setRunsError(describeError(e, 'Could not load past runs')))
  }
  useEffect(() => { loadRuns() }, [])

  async function run(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const r = await api.post('/bench/run', { size: Number(size), images: Number(images), repeats: Number(repeats) })
      setResult(r.data)
      toast({ tone: 'ok', title: 'Benchmark finished', body: `${r.data.images} images at ${r.data.size}×${r.data.size}` })
      loadRuns()
    } catch (err) {
      setError(describeError(err, 'Benchmark failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader eyebrow="speed · same images, same machine"
        title="Benchmark"
        subtitle="SkyCipher against AES-256-CTR and ChaCha20 on the same drone images. Times are the mean of the repeats, per image." />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card title="Run">
            <form onSubmit={run} className="space-y-4">
              <Select id="bench-size" label="Image size (square)" value={size} onChange={(e) => setSize(e.target.value)}
                options={SIZES.map((s) => [String(s), `${s} × ${s}`])} />
              <Input id="bench-images" type="number" min={1} max={20} label="Images (1 to 20)" value={images}
                onChange={(e) => setImages(e.target.value)} error={imagesOk ? undefined : 'Use 1 to 20'} />
              <Input id="bench-repeats" type="number" min={1} max={10} label="Repeats (1 to 10)" value={repeats}
                onChange={(e) => setRepeats(e.target.value)} error={repeatsOk ? undefined : 'Use 1 to 10'}
                hint="The first images of the bundled VisDrone set are used." />
              <Button type="submit" size="lg" icon={Play} loading={busy} disabled={!canRun} className="w-full">Run benchmark</Button>
              {error && <ErrorState error={error} compact />}
            </form>
          </Card>
        </div>

        <div className="min-w-0 space-y-5">
          {busy && (
            <Card title="Running">
              <div className="space-y-3"><Skeleton className="h-64 w-full" /><Skeleton className="h-40 w-full" /></div>
            </Card>
          )}

          {!busy && !result && (
            <Card>
              <EmptyState icon={Gauge} title="No benchmark on screen"
                body="Choose a size and run it, or open a past run below." />
            </Card>
          )}

          {result && !busy && (
            <Card title={`Run #${result.id}`} eyebrow={when(result.created_at)}>
              <KeyValueList cols={2} items={[
                ['Image size', `${result.size} × ${result.size}`],
                ['Images × repeats', `${result.images} × ${result.repeats}`],
                ['Bytes per image', `${result.bytes_per_image.toLocaleString('en-GB')} B`],
                ['CPU threads', String(result.cpu)],
              ]} />
              <div className="mt-5"><BenchChart rows={result.results} label="Encrypt and decrypt time per image, lower is better" /></div>
              <div className="mt-5 -mx-4 overflow-x-auto px-4">
                <ResultsTable rows={result.results} />
              </div>
            </Card>
          )}

          <Card title="Past runs" bodyClass="p-0">
            <div className="px-4 pb-4 pt-3">
              {runsError && <ErrorState error={runsError} compact onRetry={loadRuns} />}
              <Table
                loading={!runs && !runsError}
                rowKey={(r) => r.id}
                rows={runs}
                empty={<EmptyState title="No runs yet" body="Run the benchmark: each run is saved here." />}
                columns={[
                  { key: 'when', label: 'When', render: (r) => when(r.created_at) },
                  { key: 'size', label: 'Size', render: (r) => `${r.size}²` },
                  { key: 'images', label: 'Images', align: 'right', render: (r) => `${r.images} × ${r.repeats}` },
                  { key: 'sky', label: 'SkyCipher enc', align: 'right', render: (r) => `${num(r.results[0]?.enc_ms, 1)} ms` },
                  { key: 'aes', label: 'AES enc', align: 'right', render: (r) => `${num(r.results[1]?.enc_ms, 2)} ms` },
                  { key: 'cha', label: 'ChaCha enc', align: 'right', render: (r) => `${num(r.results[2]?.enc_ms, 2)} ms` },
                  { key: 'open', label: '', align: 'right', render: (r) => (
                    <Button size="sm" variant="ghost" onClick={() => setResult(r)}>Open</Button>
                  ) },
                ]}
              />
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}

// Per-algorithm numbers. Lossless = decrypted pixels equal the original on every image.
function ResultsTable({ rows }) {
  return (
    <Table
      rowKey={(r) => r.algorithm}
      columns={[
        { key: 'algorithm', label: 'Algorithm' },
        { key: 'enc', label: 'Encrypt', align: 'right', render: (r) => `${num(r.enc_ms, 2)} ms` },
        { key: 'dec', label: 'Decrypt', align: 'right', render: (r) => `${num(r.dec_ms, 2)} ms` },
        { key: 'encmb', label: 'Encrypt MB/s', align: 'right', render: (r) => num(r.enc_mbps, 1) },
        { key: 'decmb', label: 'Decrypt MB/s', align: 'right', render: (r) => num(r.dec_mbps, 1) },
        { key: 'fps', label: 'Frames/s (enc+dec)', align: 'right', render: (r) => num(r.fps_capacity, 1) },
        { key: 'ent', label: 'Cipher entropy', align: 'right', render: (r) => num(r.cipher_entropy, 4) },
        { key: 'corr', label: '|corr H|', align: 'right', render: (r) => num(r.cipher_corr_h, 4) },
        { key: 'lossless', label: 'Lossless', render: (r) => (r.lossless ? <Badge tone="ok">yes</Badge> : <Badge tone="alert">no</Badge>) },
      ]}
      rows={rows}
    />
  )
}

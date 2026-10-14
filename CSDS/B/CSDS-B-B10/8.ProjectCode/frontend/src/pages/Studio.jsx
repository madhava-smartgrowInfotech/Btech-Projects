import { Download, Lock, Unlock } from 'lucide-react'
import { useEffect, useState } from 'react'
import api, { describeError, download, sourceForm } from '../api'
import ImagePanel from '../components/product/ImagePanel'
import KeyField, { keyReady } from '../components/product/KeyField'
import SourcePicker from '../components/product/SourcePicker'
import { HistogramChart } from '../components/product/charts'
import { PageHeader } from '../components/ui/AppShell'
import { Button, FileDrop, Input, Select } from '../components/ui/controls'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import Table from '../components/ui/Table'
import { flipBit, HEX32, ms, num, when } from '../format'

const BANDS = ['LH', 'HL', 'HH']

export default function Studio() {
  const toast = useToast()

  // encrypt
  const [src, setSrc] = useState({})
  const [key, setKey] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // saved jobs
  const [jobs, setJobs] = useState(null)
  const [jobsError, setJobsError] = useState(null)

  // decrypt a saved job
  const [decJob, setDecJob] = useState('')
  const [decKey, setDecKey] = useState('')
  const [decBusy, setDecBusy] = useState(null) // 'ok' | 'wrong' while a request runs
  const [decError, setDecError] = useState(null)
  const [decResult, setDecResult] = useState(null)

  // decrypt an uploaded cipher file
  const [file, setFile] = useState(null)
  const [nonce, setNonce] = useState('')
  const [fileKey, setFileKey] = useState('')
  const [fileBusy, setFileBusy] = useState(false)
  const [fileError, setFileError] = useState(null)
  const [fileResult, setFileResult] = useState(null)

  const ready = !!(src.file || src.kind)

  function loadJobs() {
    return api.get('/studio/jobs')
      .then((r) => { setJobs(r.data); setJobsError(null) })
      .catch((e) => setJobsError(describeError(e, 'Could not load saved jobs')))
  }
  useEffect(() => { loadJobs() }, [])

  async function encrypt(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setResult(null)
    setDecResult(null)
    try {
      const r = await api.post('/studio/encrypt', sourceForm(src, key))
      setResult(r.data)
      setKey(r.data.key)
      setDecJob(String(r.data.job.id))
      setDecKey(r.data.key)
      toast({ tone: 'ok', title: 'Encrypted and saved', body: `job #${r.data.job.id} · ${r.data.job.width}×${r.data.job.height}` })
      loadJobs()
    } catch (err) {
      setError(describeError(err, 'Encryption failed'))
    } finally {
      setBusy(false)
    }
  }

  async function decrypt(wrong) {
    const fd = new FormData()
    fd.append('key', wrong ? flipBit(decKey) : decKey)
    fd.append('job_id', decJob)
    setDecBusy(wrong ? 'wrong' : 'ok')
    setDecError(null)
    try {
      const r = await api.post('/studio/decrypt', fd)
      setDecResult({ wrong, ...r.data })
      if (!wrong) {
        toast(r.data.match
          ? { tone: 'ok', title: 'Checksum matches', body: 'decrypted pixels are identical to the original' }
          : { tone: 'alert', title: 'Checksum does not match', body: 'the key or the stored job does not fit' })
      }
    } catch (err) {
      setDecError(describeError(err, 'Decryption failed'))
    } finally {
      setDecBusy(null)
    }
  }

  async function decryptFile(e) {
    e.preventDefault()
    const fd = new FormData()
    fd.append('file', file)
    fd.append('nonce', nonce)
    fd.append('key', fileKey)
    setFileBusy(true)
    setFileError(null)
    setFileResult(null)
    try {
      const r = await api.post('/studio/decrypt', fd)
      setFileResult(r.data)
    } catch (err) {
      setFileError(describeError(err, 'Decryption failed'))
    } finally {
      setFileBusy(false)
    }
  }

  async function downloadPng(job) {
    try {
      await download(`/studio/jobs/${job.id}/cipher.png`, `cipher_${job.id}_${job.nonce}.png`)
      toast({ tone: 'ok', title: 'Cipher PNG downloaded', body: `job #${job.id}` })
    } catch (err) {
      toast({ tone: 'alert', title: 'Download failed', body: describeError(err).message })
    }
  }

  const decReady = !!decJob && keyReady(decKey) && !decBusy
  const fileReady = !!file && HEX32.test(nonce) && keyReady(fileKey) && !fileBusy

  return (
    <>
      <PageHeader eyebrow="encrypt · decrypt"
        title="Image studio"
        subtitle="Encrypt a drone image and inspect every stage: wavelet sub-bands, the cipher image and both histograms. Then check that decryption restores it bit for bit." />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,360px)_minmax(0,1fr)]">
        <div className="space-y-5">
          <Card title="1 · Image">
            <SourcePicker value={src} onChange={setSrc} id="studio-source" />
          </Card>
          <Card title="2 · Key">
            <KeyField id="enc-key" value={key} onChange={setKey} optional />
            <p className="mt-2 text-xs text-muted">Leave it empty to make a new key. Keep the key: decryption needs it.</p>
          </Card>
          <form onSubmit={encrypt} className="space-y-3">
            <Button type="submit" size="lg" icon={Lock} loading={busy} disabled={!ready || !keyReady(key, true)} className="w-full">
              Encrypt image
            </Button>
            {!ready && <p className="text-center font-mono text-[11px] text-dim">choose an image to enable encryption</p>}
            {error && <ErrorState error={error} />}
          </form>
        </div>

        <div className="min-w-0 space-y-5">
          {busy && (
            <Card title="Encrypting">
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /><Skeleton className="aspect-square" /></div>
            </Card>
          )}

          {!busy && !result && (
            <Card>
              <EmptyState icon={Lock} title="No encryption yet"
                body="Pick an image and press Encrypt. The result shows the wavelet sub-bands, the cipher image and the histograms before and after." />
            </Card>
          )}

          {result && (
            <Card title={`Encryption result · job #${result.job.id}`} eyebrow={result.resized ? 'image resized to fit 1024 px' : 'original resolution'}>
              <KeyValueList cols={2} items={[
                ['Image', result.job.name],
                ['Size', `${result.job.width} × ${result.job.height}, ${result.job.channels} channel${result.job.channels > 1 ? 's' : ''}`],
                ['Nonce', <code key="n" className="break-all">{result.job.nonce}</code>],
                ['Key fingerprint', <code key="f" className="break-all">{result.job.key_fp}</code>],
                ['Key setup (once per key)', ms(result.key_setup_ms)],
                ['Encryption', ms(result.job.enc_ms)],
              ]} />

              <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
                <ImagePanel src={result.plain} caption="Original" />
                <ImagePanel src={result.cipher} caption="Cipher" />
                <ImagePanel src={result.coefficients} caption="Wavelet coefficients" />
                <ImagePanel src={result.subbands.LL} caption="Sub-band LL" />
                {BANDS.map((b) => <ImagePanel key={b} src={result.subbands[b]} caption={`Sub-band ${b}`} />)}
              </div>

              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <div>
                  <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-dim">Original histogram</div>
                  <HistogramChart hist={result.histograms.plain} label="Original histogram" />
                </div>
                <div>
                  <div className="mb-2 font-mono text-[11px] uppercase tracking-[0.12em] text-dim">Cipher histogram</div>
                  <HistogramChart hist={result.histograms.cipher} label="Cipher histogram" />
                </div>
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                <Button variant="secondary" icon={Download} onClick={() => downloadPng(result.job)}>Download cipher PNG</Button>
              </div>
            </Card>
          )}

          <Card title="Decrypt a saved job" eyebrow="checksum check">
            {jobs === null && !jobsError ? <Skeleton className="h-40 w-full" /> : (
              <div className="space-y-4">
                {jobsError && <ErrorState error={jobsError} compact onRetry={loadJobs} />}
                <Select id="dec-job" label="Encrypted image" value={decJob}
                  onChange={(e) => { setDecJob(e.target.value); setDecResult(null) }}
                  options={[['', jobs?.length ? 'choose a job…' : 'no saved jobs yet'],
                    ...(jobs || []).map((j) => [String(j.id), `#${j.id} · ${j.name} · ${j.width}×${j.height}`])]} />
                <KeyField id="dec-key" value={decKey} onChange={(v) => { setDecKey(v); setDecResult(null) }}
                  label="Key used to encrypt this image" allowNew={false} />
                <div className="flex flex-wrap gap-2">
                  <Button icon={Unlock} loading={decBusy === 'ok'} disabled={!decReady} onClick={() => decrypt(false)}>Decrypt</Button>
                  <Button variant="secondary" icon={Lock} loading={decBusy === 'wrong'} disabled={!decReady} onClick={() => decrypt(true)}>
                    Try a key with 1 bit flipped
                  </Button>
                </div>
                {decError && <ErrorState error={decError} compact />}
                {decResult && <DecryptResult r={decResult} />}
              </div>
            )}
          </Card>

          <Card title="Decrypt a cipher file" eyebrow="upload + nonce">
            <form onSubmit={decryptFile} className="space-y-4">
              <FileDrop label="Drop a cipher PNG here" accept="image/png" multiple={false}
                onFiles={(files) => setFile(files[0] || null)} />
              <Input id="file-nonce" label="Nonce (32 hex characters)" value={nonce} onChange={(e) => setNonce(e.target.value.trim())}
                spellCheck={false} autoComplete="off" maxLength={32} className="font-mono"
                error={nonce && !HEX32.test(nonce) ? 'Needs exactly 32 hex characters' : undefined}
                hint="The downloaded PNG is named cipher_<job>_<nonce>.png, so the nonce is in its file name." />
              <KeyField id="file-key" value={fileKey} onChange={setFileKey} label="Key" allowNew={false} />
              <Button type="submit" icon={Unlock} loading={fileBusy} disabled={!fileReady}>Decrypt file</Button>
              {fileError && <ErrorState error={fileError} compact />}
              {fileResult && (
                <div className="space-y-3 rounded-[6px] border border-line p-3">
                  <ImagePanel src={fileResult.decrypted} caption="Decrypted" className="max-w-xs" />
                  <KeyValueList items={[['SHA-256 of decrypted pixels', <code key="s" className="break-all">{fileResult.sha256}</code>],
                    ['Decryption time', ms(fileResult.dec_ms)]]} />
                  <p className="text-xs text-muted">Uploaded cipher files have no stored checksum. Compare the result with the original yourself.</p>
                </div>
              )}
            </form>
          </Card>

          <Card title="Recent encryptions" bodyClass="p-0">
            <div className="px-4 pb-4 pt-3">
              {jobsError && !jobs && <ErrorState error={jobsError} compact onRetry={loadJobs} />}
              <Table
                loading={!jobs && !jobsError}
                rowKey={(j) => j.id}
                rows={jobs}
                empty={<EmptyState title="No encrypted images yet" body="Encrypt an image above and it appears here." />}
                columns={[
                  { key: 'id', label: '#', render: (j) => <span className="font-mono">{j.id}</span> },
                  { key: 'name', label: 'Image', className: 'max-w-[200px] truncate' },
                  { key: 'size', label: 'Size', render: (j) => `${j.width}×${j.height}` },
                  { key: 'created', label: 'Created', render: (j) => when(j.created_at) },
                  { key: 'actions', label: '', align: 'right', render: (j) => (
                    <span className="inline-flex gap-1.5">
                      <Button size="sm" variant="ghost" icon={Download} onClick={() => downloadPng(j)}>PNG</Button>
                      <Button size="sm" variant="ghost" icon={Unlock} onClick={() => { setDecJob(String(j.id)); setDecResult(null) }}>Decrypt</Button>
                    </span>
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

// Result of a checksum decrypt. A wrong key is expected to fail: that is the test.
function DecryptResult({ r }) {
  let badge
  if (r.wrong) badge = <Badge tone={r.match === false ? 'alert' : 'warn'}>{r.match === false ? 'wrong key: decryption failed' : 'unexpected match'}</Badge>
  else if (r.match === true) badge = <Badge tone="ok" dot>checksum matches</Badge>
  else if (r.match === false) badge = <Badge tone="alert" dot>checksum does not match</Badge>
  else badge = <Badge>no stored checksum</Badge>
  return (
    <div className="space-y-3 rounded-[6px] border border-line p-3">
      <div className="flex flex-wrap items-center gap-2">
        {badge}
        {r.wrong && <span className="text-xs text-muted">Flipping one key bit should turn the image into noise.</span>}
      </div>
      <ImagePanel src={r.decrypted} caption={r.wrong ? 'Decrypted with 1-bit-wrong key' : 'Decrypted'} className="max-w-xs" />
      <KeyValueList items={[
        ['SHA-256 of decrypted pixels', <code key="s" className="break-all">{r.sha256}</code>],
        ['SHA-256 stored with the job', r.expected_sha256 ? <code key="e" className="break-all">{r.expected_sha256}</code> : '—'],
        ['Key matches the job', r.key_matches_job === null ? '—' : r.key_matches_job ? 'yes' : 'no'],
        ['Decryption time', ms(r.dec_ms)],
        ['Mean brightness (decrypted)', num(meanOf(r.histogram), 1)],
      ]} />
    </div>
  )
}

// Mean pixel value from a histogram ({ gray: [256] } or { r, g, b }).
function meanOf(hist) {
  const bins = hist?.gray || hist?.r
  if (!bins) return null
  const total = bins.reduce((a, b) => a + b, 0)
  if (!total) return null
  return bins.reduce((a, c, v) => a + c * v, 0) / total
}

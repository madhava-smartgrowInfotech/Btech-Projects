import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Download, ImageIcon, Send as SendIcon } from 'lucide-react'
import api, { describeError, download, fmtBytes, fmtMs } from '../api'
import AuthImage from '../components/AuthImage'
import { PageHeader } from '../components/ui/AppShell'
import { Button, FileDrop, Select } from '../components/ui/controls'
import { Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, ProgressBar, Skeleton, useToast } from '../components/ui/feedback'
import { Stepper, Tabs } from '../components/ui/nav'
import Hash from '../components/Hash'

const SAMPLE = 'sample'
const UPLOAD = 'upload'
const SOURCE_TABS = [{ id: SAMPLE, label: 'Sample' }, { id: UPLOAD, label: 'Upload' }]
const STEPS = [{ id: 'key', label: 'Key' }, { id: 'file', label: 'File' }, { id: 'cover', label: 'Cover' }, { id: 'hide', label: 'Hide' }]

export default function Send() {
  const navigate = useNavigate()
  const toast = useToast()
  const [keys, setKeys] = useState(null)
  const [covers, setCovers] = useState(null)
  const [payloads, setPayloads] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [keyId, setKeyId] = useState('')
  const [payloadMode, setPayloadMode] = useState(SAMPLE)
  const [payloadSample, setPayloadSample] = useState('')
  const [payloadFile, setPayloadFile] = useState(null)
  const [coverMode, setCoverMode] = useState(SAMPLE)
  const [coverSample, setCoverSample] = useState('')
  const [coverFile, setCoverFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [sendError, setSendError] = useState(null)
  const [result, setResult] = useState(null)

  const loadAll = () => {
    setLoadError(null)
    return Promise.all([api.get('/keys'), api.get('/samples/covers'), api.get('/samples/payloads')])
      .then(([k, c, p]) => {
        setKeys(k.data)
        setCovers(c.data)
        setPayloads(p.data)
        if (k.data[0]) setKeyId((cur) => cur || String(k.data[0].id))
        if (c.data[0]) setCoverSample((cur) => cur || c.data[0].name)
        if (p.data[0]) setPayloadSample((cur) => cur || p.data[0].name)
      })
      .catch((e) => setLoadError(describeError(e)))
  }
  useEffect(() => { loadAll() }, [])

  // bundle = file + RSA-wrapped session key + header; estimated here, the server checks for real
  const key = keys?.find((k) => String(k.id) === keyId)
  const payloadSize = payloadMode === UPLOAD ? payloadFile?.size : payloads?.find((p) => p.name === payloadSample)?.size
  const cover = covers?.find((c) => c.name === coverSample)
  const coverCap = coverMode === SAMPLE ? cover?.capacity_bytes : null
  const estimate = payloadSize != null && key ? payloadSize + key.bits / 8 + 170 : null
  const pct = estimate != null && coverCap ? (estimate / coverCap) * 100 : null
  const payloadReady = payloadMode === UPLOAD ? !!payloadFile : !!payloadSample
  const coverReady = coverMode === UPLOAD ? !!coverFile : !!coverSample
  const ready = !!keyId && payloadReady && coverReady
  const stage = !keyId ? 'key' : !payloadReady ? 'file' : !coverReady ? 'cover' : 'hide'

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setSendError(null)
    setResult(null)
    const fd = new FormData()
    fd.append('key_id', keyId)
    if (payloadMode === UPLOAD) fd.append('payload', payloadFile)
    else fd.append('payload_sample', payloadSample)
    if (coverMode === UPLOAD) fd.append('cover', coverFile)
    else fd.append('cover_sample', coverSample)
    try {
      const { data } = await api.post('/send', fd)
      setResult(data)
      toast({ tone: 'ok', title: 'Stego PNG ready', body: `Operation #${data.op_id}. Download it or open its analysis.` })
    } catch (err) {
      setSendError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Send"
        subtitle="Encrypt a file for a receiver and hide the result inside a cover image. The output is always a PNG." />

      {loadError && <div className="mb-4"><ErrorState error={loadError} onRetry={loadAll} /></div>}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card title="Message" className="lg:col-span-2" bodyClass="space-y-5 p-4">
          {keys === null && !loadError && <Skeleton className="h-64 w-full" />}
          {keys?.length === 0 && (
            <EmptyState icon={KeyRound} title="No receiver key yet" body="Sending needs a recipient's public key. Create one or import theirs first."
              action={<Link to="/keys" className="inline-flex h-9 items-center rounded-[6px] border border-line-strong bg-panel-2 px-3.5 text-sm text-fg hover:border-ok/60 hover:text-ok">Go to Keys</Link>} />
          )}
          {keys?.length > 0 && (
            <form onSubmit={submit} className="space-y-5">
              <Stepper steps={STEPS} current={stage} done={!!result} failed={!!sendError && !busy} />

              <Select label="Receiver's key" value={keyId} onChange={(e) => setKeyId(e.target.value)}
                options={keys.map((k) => [String(k.id), `${k.name} (${k.bits}-bit${k.has_private ? '' : ', public only'})`])} />

              <div className="space-y-2">
                <Tabs id="payload-src" tabs={SOURCE_TABS} value={payloadMode} onChange={setPayloadMode} label="File source" />
                {payloadMode === SAMPLE ? (
                  <Select label="File to protect" value={payloadSample} onChange={(e) => setPayloadSample(e.target.value)}
                    options={(payloads || []).map((p) => [p.name, `${p.name} · ${fmtBytes(p.size_bytes)}`])} />
                ) : (
                  <FileDrop label="Drop the file to protect" multiple={false} onFiles={(f) => setPayloadFile(f[0] || null)} />
                )}
              </div>

              <div className="space-y-2">
                <Tabs id="cover-src" tabs={SOURCE_TABS} value={coverMode} onChange={setCoverMode} label="Cover image source" />
                {coverMode === SAMPLE ? (
                  <Select label="Cover image" value={coverSample} onChange={(e) => setCoverSample(e.target.value)}
                    options={(covers || []).map((c) => [c.name, `${c.name} · holds ${fmtBytes(c.capacity_bytes)}`])} />
                ) : (
                  <FileDrop label="Drop a cover image" accept="image/*" multiple={false} onFiles={(f) => setCoverFile(f[0] || null)} />
                )}
              </div>

              {pct != null && (
                <div className="space-y-2">
                  <ProgressBar value={Math.min(pct, 100)} tone={pct > 100 ? 'alert' : 'ok'}
                    label={`Capacity estimate · ${fmtBytes(Math.round(estimate))} of ${fmtBytes(coverCap)}`} />
                  {pct > 100 && <p className="text-xs text-alert">Too large for this cover. Choose a bigger image or a smaller file.</p>}
                </div>
              )}

              <ErrorState error={sendError} />
              <Button type="submit" size="lg" className="w-full" icon={SendIcon} loading={busy} disabled={!ready}>
                Encrypt and hide
              </Button>
            </form>
          )}
        </Card>

        <div className="lg:col-span-3">
          <Card title="Stego image" eyebrow={result ? `operation #${result.op_id}` : undefined} bodyClass="space-y-5 p-4">
            {!result && !busy && (
              <EmptyState icon={ImageIcon} title="No output yet"
                body="The stego PNG, its quality measures and a hash of your file appear here after you run Encrypt and hide." />
            )}
            {busy && <Skeleton className="h-72 w-full" />}
            {result && (
              <>
                <AuthImage path={`/ops/${result.op_id}/stego`} alt="Stego image with hidden data"
                  className="max-h-72 w-full rounded-[6px] border border-line object-contain" />
                <div className="flex flex-wrap gap-2">
                  <Button icon={Download} onClick={() => download(`/ops/${result.op_id}/stego`, `stego_${result.op_id}.png`)}>Download PNG</Button>
                  <Button variant="secondary" onClick={() => navigate(`/analysis?op=${result.op_id}`)}>Open analysis</Button>
                  <Button variant="ghost" onClick={() => navigate(`/receive?op=${result.op_id}`)}>Try receiving it</Button>
                </div>
                <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                  <StatCard label="PSNR" value={`${result.quality.psnr_db} dB`} tone="ok" sub="above 50 dB is invisible" />
                  <StatCard label="SSIM" value={String(result.quality.ssim)} tone="ok" sub="1 = identical" />
                  <StatCard label="Capacity used" value={`${result.capacity.used_pct}%`} sub={`${result.capacity.payload_bits_per_pixel} bits/pixel`} />
                  <StatCard label="Hidden" value={fmtBytes(result.bundle_bytes)} sub={`from a ${fmtBytes(result.payload_bytes)} file`} />
                </div>
                <Hash label="SHA-256 of the file you sent" value={result.input_sha256} />
                <KeyValueList cols={2} items={[
                  ['Encrypt', fmtMs(result.timings_ms.encrypt)], ['Embed', fmtMs(result.timings_ms.embed)],
                  ['PNG encode', fmtMs(result.timings_ms.png_encode)], ['Metrics', fmtMs(result.timings_ms.metrics)],
                ]} />
              </>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}

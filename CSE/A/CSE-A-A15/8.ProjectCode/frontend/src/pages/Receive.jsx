import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Download, KeyRound, ShieldCheck, XCircle } from 'lucide-react'
import api, { describeError, download, fmtBytes, fmtMs } from '../api'
import Hash from '../components/Hash'
import { PageHeader } from '../components/ui/AppShell'
import { Button, FileDrop, Select } from '../components/ui/controls'
import { Badge, Card, KeyValueList, StatCard } from '../components/ui/display'
import { EmptyState, ErrorState, Skeleton, useToast } from '../components/ui/feedback'
import { Stepper, Tabs } from '../components/ui/nav'

const SENT = 'sent'
const UPLOAD = 'upload'
const SOURCE_TABS = [{ id: SENT, label: 'Pick one I sent' }, { id: UPLOAD, label: 'Upload a file' }]
const STEPS = [{ id: 'key', label: 'Key' }, { id: 'image', label: 'Image' }, { id: 'extract', label: 'Extract' }, { id: 'verify', label: 'Verify' }]

export default function Receive() {
  const [params] = useSearchParams()
  const toast = useToast()
  const [keys, setKeys] = useState(null)
  const [sent, setSent] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [keyId, setKeyId] = useState('')
  const [mode, setMode] = useState(params.get('op') ? SENT : UPLOAD)
  const [file, setFile] = useState(null)
  const [fromOp, setFromOp] = useState(params.get('op') || '')
  const [busy, setBusy] = useState(false)
  const [recvError, setRecvError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    Promise.all([api.get('/keys'), api.get('/log', { params: { op: 'send', limit: 50 } })])
      .then(([k, l]) => {
        const own = k.data.filter((x) => x.has_private)
        setKeys(own)
        if (own[0]) setKeyId(String(own[0].id))
        const ok = l.data.filter((x) => x.ok)
        setSent(ok)
        if (!params.get('op') && ok[0]) setFromOp(String(ok[0].id))
        const wanted = ok.find((x) => String(x.id) === params.get('op'))
        if (wanted) setKeyId(String(wanted.details.key_id))
      })
      .catch((e) => setLoadError(describeError(e)))
    // loads once; the ?op= param is read from the first render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const ready = !!keyId && (mode === UPLOAD ? !!file : !!fromOp)
  const stage = !keyId ? 'key' : !ready ? 'image' : result ? 'verify' : 'extract'

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setRecvError(null)
    setResult(null)
    const fd = new FormData()
    fd.append('key_id', keyId)
    if (mode === UPLOAD) fd.append('stego', file)
    else fd.append('from_op', fromOp)
    try {
      const { data } = await api.post('/receive', fd)
      setResult(data)
      toast({
        tone: data.hash_match ? 'ok' : 'alert',
        title: data.hash_match ? 'Restored byte for byte' : 'Hash mismatch',
        body: data.hash_match ? `${data.filename} is ready to download.` : 'The restored file does not match the hash recorded at send time.',
      })
    } catch (err) {
      setRecvError(describeError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Receive"
        subtitle="Extract the hidden bundle from a stego image, unwrap the session key with your private key, verify the AES-GCM tag and restore the file." />

      {loadError && <div className="mb-4"><ErrorState error={loadError} /></div>}

      <div className="grid gap-4 lg:grid-cols-5">
        <Card title="Open a message" className="lg:col-span-2" bodyClass="space-y-5 p-4">
          {keys === null && !loadError && <Skeleton className="h-64 w-full" />}
          {keys?.length === 0 && (
            <EmptyState icon={KeyRound} title="No keypair to open with" body="Receiving needs one of your own keypairs, because only the private half can unwrap the key."
              action={<Link to="/keys" className="inline-flex h-9 items-center rounded-[6px] border border-line-strong bg-panel-2 px-3.5 text-sm text-fg hover:border-ok/60 hover:text-ok">Go to Keys</Link>} />
          )}
          {keys?.length > 0 && (
            <form onSubmit={submit} className="space-y-5">
              <Stepper steps={STEPS} current={stage} done={!!result} failed={!!recvError && !busy} />

              <Select label="Your private key" value={keyId} onChange={(e) => setKeyId(e.target.value)}
                options={keys.map((k) => [String(k.id), `${k.name} (${k.bits}-bit)`])} />

              <div className="space-y-2">
                <Tabs id="stego-src" tabs={SOURCE_TABS} value={mode} onChange={setMode} label="Stego image source" />
                {mode === UPLOAD ? (
                  <FileDrop label="Drop the stego PNG" accept="image/png,image/*" multiple={false} onFiles={(f) => setFile(f[0] || null)} />
                ) : sent?.length ? (
                  <Select label="Sent image" value={fromOp} onChange={(e) => setFromOp(e.target.value)}
                    options={sent.map((s) => [String(s.id), `#${s.id} · ${s.details.filename} in ${s.details.cover}`])} />
                ) : (
                  <p className="text-sm text-muted">Nothing sent yet. <Link to="/send" className="text-ok hover:underline">Encrypt a file first</Link>, or upload a PNG instead.</p>
                )}
              </div>

              <ErrorState error={recvError} />
              <Button type="submit" size="lg" className="w-full" icon={ShieldCheck} loading={busy} disabled={!ready}>
                Extract and decrypt
              </Button>
            </form>
          )}
        </Card>

        <div className="lg:col-span-3">
          <Card title="Restored file" eyebrow={result ? `operation #${result.op_id}` : undefined} bodyClass="space-y-5 p-4">
            {!result && !busy && (
              <EmptyState icon={ShieldCheck} title="Nothing restored yet"
                body="The restored file, the two SHA-256 hashes and their comparison appear here." />
            )}
            {busy && <Skeleton className="h-64 w-full" />}
            {result && (
              <>
                <div className="flex flex-wrap items-center gap-3">
                  {result.hash_match
                    ? <CheckCircle2 className="h-6 w-6 text-ok" aria-hidden="true" />
                    : <XCircle className="h-6 w-6 text-alert" aria-hidden="true" />}
                  <h2 className={`font-mono text-base font-semibold ${result.hash_match ? 'text-ok' : 'text-alert'}`}>
                    {result.hash_match ? 'Restored byte for byte' : 'Hash mismatch'}
                  </h2>
                  <Badge tone="ok" dot>AES-GCM tag verified</Badge>
                </div>
                <KeyValueList items={[['File', result.filename], ['Size', fmtBytes(result.output_bytes)], ['Source', result.source]]} />
                <div className="grid gap-4 sm:grid-cols-2">
                  <Hash label="SHA-256 recorded at send time" value={result.embedded_sha256} ok={result.hash_match} />
                  <Hash label="SHA-256 of the restored file" value={result.output_sha256} ok={result.hash_match} />
                </div>
                <Button icon={Download} onClick={() => download(`/ops/${result.op_id}/restored`, result.filename)}>
                  Download {result.filename}
                </Button>
                <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                  <StatCard label="Extract" value={fmtMs(result.timings_ms.extract)} />
                  <StatCard label="Decrypt" value={fmtMs(result.timings_ms.decrypt)} />
                  <StatCard label="Bundle" value={fmtBytes(result.bundle_bytes)} />
                  <StatCard label="File" value={fmtBytes(result.output_bytes)} />
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}

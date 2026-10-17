import { CheckCircle2, Copy, Lock, ShieldOff, Unlock, Undo2 } from 'lucide-react'
import { useState } from 'react'
import api, { describeError } from '../api'
import { PageHeader } from '../components/ui/AppShell'
import { Button, FileDrop, Textarea } from '../components/ui/controls'
import { Badge, Card, KeyValueList } from '../components/ui/display'
import { EmptyState, ErrorState, useToast } from '../components/ui/feedback'
import { Stepper, TabPanel, Tabs } from '../components/ui/nav'
import { bytes } from '../format'
import { logEvent } from '../lib/activity'

const STEPS = [
  { id: 'ecdh', label: 'ECDH P-256' },
  { id: 'hkdf', label: 'HKDF-SHA256' },
  { id: 'gcm', label: 'AES-256-GCM' },
  { id: 'cloud', label: 'Cloud verify' },
]
const MAX_FILE = 5 * 1024 * 1024
const SAMPLE = 'Confidential payload for cloud storage: Q4 customer ledger export'

function Mono({ label, value }) {
  const toast = useToast()
  async function copy() {
    try {
      await navigator.clipboard.writeText(value)
      toast({ tone: 'ok', title: `${label} copied` })
    } catch {
      toast({ tone: 'warn', title: 'Copy blocked by the browser', body: 'Select the text and copy it manually.' })
    }
  }
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{label}</span>
        <button type="button" onClick={copy} aria-label={`Copy ${label}`} className="rounded p-1 text-dim hover:text-ok"><Copy size={13} /></button>
      </div>
      <pre tabIndex={0} className="max-h-28 overflow-auto whitespace-pre-wrap break-all rounded-[6px] border border-line bg-panel-2 p-2 font-mono text-[11px] leading-relaxed text-fg">{value}</pre>
    </div>
  )
}

export default function SecureTransfer() {
  const toast = useToast()
  const [tab, setTab] = useState('text')
  const [text, setText] = useState(SAMPLE)
  const [file, setFile] = useState(null)
  const [inputError, setInputError] = useState(null)
  const [encrypting, setEncrypting] = useState(false)
  const [encError, setEncError] = useState(null)
  const [enc, setEnc] = useState(null) // API response + { kind, name }
  const [ct, setCt] = useState('') // ciphertext as it will be sent for decryption (can be tampered)
  const [tampered, setTampered] = useState(false)
  const [decrypting, setDecrypting] = useState(false)
  const [dec, setDec] = useState(null) // { ok, plaintext } | { ok:false, error }

  const stage = dec ? (dec.ok ? 'verified' : 'failed') : enc ? 'encrypted' : encrypting ? 'encrypting' : 'idle'

  function pickFile(files) {
    const f = files[0]
    setInputError(null)
    if (!f) { setFile(null); return }
    if (f.size === 0) { setFile(null); setInputError('That file is empty.'); return }
    if (f.size > MAX_FILE) { setFile(null); setInputError('That file is over the 5 MB limit.'); return }
    setFile(f)
  }

  async function encrypt() {
    setInputError(null)
    setEncError(null)
    if (tab === 'text' && !text.trim()) { setInputError('Enter some text to encrypt.'); return }
    if (tab === 'file' && !file) { setInputError('Choose a file to encrypt.'); return }
    setEncrypting(true)
    setDec(null)
    setTampered(false)
    try {
      let data
      if (tab === 'text') {
        data = (await api.post('/crypto/encrypt', { plaintext: text })).data
        data.kind = 'text'
        data.name = 'message'
        data.original_size = new TextEncoder().encode(text).length
        data.encrypted_size = atob(data.ciphertext).length
      } else {
        const fd = new FormData()
        fd.append('file', file)
        data = (await api.post('/crypto/encrypt-file', fd)).data
        data.kind = 'file'
        data.name = data.filename
      }
      setEnc(data)
      setCt(data.ciphertext)
      logEvent('crypto', `encrypted ${data.name} (${bytes(data.original_size)}) with ECDH P-256 + HKDF + AES-256-GCM`)
      toast({ tone: 'ok', title: 'Encrypted for the cloud', body: `${bytes(data.original_size)} in, ${bytes(data.encrypted_size)} of ciphertext out.` })
    } catch (e) {
      setEnc(null)
      setEncError(describeError(e))
    } finally {
      setEncrypting(false)
    }
  }

  async function decrypt(cipher = ct) {
    setDecrypting(true)
    try {
      const { data } = await api.post('/crypto/decrypt', { ciphertext: cipher, nonce: enc.nonce, tag: enc.tag, ephemeral_public: enc.ephemeral_public })
      setDec({ ok: true, plaintext: data.plaintext, verified: data.verified })
      logEvent('crypto', 'cloud derived the session key via ECDH and verified the GCM tag')
      toast({ tone: 'ok', title: 'Tag verified', body: 'The cloud decrypted the payload.' })
    } catch (e) {
      const d = describeError(e)
      setDec({ ok: false, error: d })
      logEvent('error', 'GCM tag verification failed at the cloud')
      toast({ tone: 'alert', title: 'Decryption rejected', body: 'Authentication failed.' })
    } finally {
      setDecrypting(false)
    }
  }

  function tamper() {
    // changing the first base64 character always changes the first ciphertext byte
    const flipped = (ct[0] === 'A' ? 'B' : 'A') + ct.slice(1)
    setCt(flipped)
    setTampered(true)
    decrypt(flipped)
  }

  function restore() {
    setCt(enc.ciphertext)
    setTampered(false)
    setDec(null)
  }

  const stepper = {
    idle: { current: null }, encrypting: { current: 'gcm' }, encrypted: { current: 'cloud' },
    verified: { done: true }, failed: { current: 'cloud', failed: true },
  }[stage]

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="SecureChannel" title="Secure transfer"
        subtitle="Encrypt a payload before it leaves for the cloud: an ephemeral ECDH P-256 key pair, HKDF-SHA256 to derive the key, AES-256-GCM to seal the data. Then let the mock cloud verify it - or tamper with it and watch the tag check fail." />
      <Card bodyClass="p-4"><Stepper steps={STEPS} {...stepper} /></Card>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Encrypt and transmit" eyebrow="POST /api/crypto/encrypt">
          <Tabs id="enc" tabs={[{ id: 'text', label: 'Text' }, { id: 'file', label: 'File (max 5 MB)' }]} value={tab} onChange={(t) => { setTab(t); setInputError(null) }} label="Payload type" />
          <div className="pt-4">
            <TabPanel tabsId="enc" value={tab}>
              {tab === 'text' ? (
                <Textarea label="Message / payload" rows={5} value={text} onChange={(e) => { setText(e.target.value); setInputError(null) }}
                  placeholder="Enter sensitive data to encrypt..." hint="Up to 1 MB of UTF-8 text." error={tab === 'text' ? inputError : undefined} />
              ) : (
                <div className="space-y-2">
                  <FileDrop label="Drop a file to encrypt" multiple={false} onFiles={pickFile} />
                  {inputError && <p role="alert" className="text-xs text-alert">{inputError}</p>}
                </div>
              )}
            </TabPanel>
          </div>
          {encError && <div className="mt-4"><ErrorState error={encError} title="Encryption failed" onRetry={encrypt} /></div>}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Button icon={Lock} loading={encrypting} onClick={encrypt}>Encrypt and transmit to cloud</Button>
          </div>

          {enc && (
            <div className="mt-5 space-y-4 border-t border-line pt-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="ok" dot>sealed</Badge>
                <span className="text-xs text-muted">{enc.algorithm || 'AES-256-GCM'}{enc.key_exchange ? ` - ${enc.key_exchange}` : ' - ECDH P-256 + HKDF-SHA256'}</span>
              </div>
              <KeyValueList items={[['Payload', enc.name], ['Plaintext size', bytes(enc.original_size)], ['Ciphertext size', bytes(enc.encrypted_size)]]} />
              <Mono label="Ciphertext (base64)" value={ct} />
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <Mono label="Nonce (12 bytes)" value={enc.nonce} />
                <Mono label="GCM tag (16 bytes)" value={enc.tag} />
              </div>
              <Mono label="Ephemeral public key" value={enc.ephemeral_public} />
            </div>
          )}
        </Card>

        <Card title="Mock cloud - decrypt and verify" eyebrow="POST /api/crypto/decrypt">
          {!enc ? (
            <EmptyState icon={Unlock} title="Nothing in transit yet" body="Encrypt a message or file on the left. The ciphertext, nonce, tag and ephemeral key arrive here for the cloud to verify."
              action={<Button variant="secondary" size="sm" icon={Lock} onClick={encrypt} loading={encrypting}>Encrypt now</Button>} />
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-muted">The cloud holds the long-term private key. It derives the same session key from your ephemeral public key, then AES-GCM checks the tag before releasing any plaintext.</p>
              {tampered && <ErrorState compact title="Ciphertext modified" error="The first ciphertext byte was changed in transit. Expect the tag check to fail." />}
              <div className="flex flex-wrap gap-2">
                <Button icon={Unlock} loading={decrypting} onClick={() => decrypt()}>Decrypt and verify at cloud</Button>
                <Button variant="danger" icon={ShieldOff} disabled={decrypting} onClick={tamper}>Tamper ciphertext</Button>
                {tampered && <Button variant="ghost" icon={Undo2} onClick={restore}>Restore original</Button>}
              </div>
              <div aria-live="polite">
                {dec?.ok && (
                  <div className="space-y-2 rounded-[6px] border border-ok/35 bg-ok/[0.07] p-4">
                    <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.12em] text-ok"><CheckCircle2 size={16} />Decrypted and verified</div>
                    <Mono label={enc.kind === 'file' ? `Recovered content of ${enc.name} (preview)` : 'Recovered plaintext'} value={dec.plaintext.length > 600 ? `${dec.plaintext.slice(0, 600)}...` : dec.plaintext || '(empty)'} />
                  </div>
                )}
                {dec && !dec.ok && <ErrorState error={dec.error} title="Decryption rejected" />}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

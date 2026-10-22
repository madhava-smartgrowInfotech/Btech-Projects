import { useNavigate } from 'react-router-dom'
import { KeyRound, LockKeyhole, LogOut, ShieldCheck } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { ROLE, when } from '../lib/format'
import { Badge, Button, Card, CardHeader, KeyValueList, PageHeader, useToast } from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'
import { useVaultKey } from '../features/UnlockGate'

const LAYERS = [
  ['Encrypted before upload', 'AES-256-GCM runs in your browser. The server receives ciphertext only.'],
  ['Keys wrapped per recipient', 'RSA-2048-OAEP (SHA-256). Sharing re-wraps the file key locally, never in plaintext.'],
  ['Integrity verified', 'SHA-256 of the plaintext plus the AES-GCM tag are checked on every download.'],
  ['Role-based access', 'Owner, Editor and Viewer are enforced by the server on every request.'],
  ['Audit trail', 'Sensitive actions are recorded in a tamper-evident hash chain.'],
]

const Status = ({ ok, yes, no }) => (
  <Badge tone={ok ? 'safe' : 'warn'} dot>
    {ok ? yes : no}
  </Badge>
)

export default function Security() {
  const { user, unlocked, lock, logout } = useAuth()
  const ensureKey = useVaultKey()
  const toast = useToast()
  const navigate = useNavigate()

  const unlock = () => ensureKey().catch(() => {})
  const doLock = () => {
    lock()
    toast({ tone: 'info', title: 'Vault locked', message: 'The private key was cleared from memory. Enter your password to unlock again.' })
  }
  const out = async () => {
    await logout()
    navigate('/')
  }

  return (
    <>
      <PageHeader crumbs={[{ label: 'Vault', to: '/app' }, { label: 'Security' }]} title="Security profile" description="Your account, your keys, and how CipherVault protects your files." />

      <div className="grid grid-2 mt" style={{ alignItems: 'start' }}>
        <SlideUp>
          <Card>
            <CardHeader title="Account" />
            <div className="card-body">
              <KeyValueList
                items={[
                  ['Name', user.name],
                  ['Email', <span className="break">{user.email}</span>],
                  ['Account role', <Badge tone={ROLE[user.role]?.tone}>{user.role}</Badge>],
                  ['Member since', when(user.created_at)],
                ]}
              />
              <div className="row mt">
                <Button variant="danger" icon={LogOut} onClick={out}>
                  Sign out
                </Button>
              </div>
            </div>
          </Card>
        </SlideUp>

        <SlideUp delay={0.05}>
          <Card>
            <CardHeader title="Keys" subtitle="RSA-2048 key pair, generated in your browser" />
            <div className="card-body">
              <KeyValueList
                items={[
                  ['Public key', <Status ok={!!user.public_key} yes="Registered" no="Missing" />],
                  ['Encrypted private key', <Status ok={user.has_private_key} yes="Stored (encrypted)" no="Missing" />],
                  ['This session', <Status ok={unlocked} yes="Unlocked in memory" no="Locked" />],
                ]}
              />
              <div className="callout mt">
                <KeyRound size={18} aria-hidden="true" />
                <span>Your private key is encrypted with PBKDF2-HMAC-SHA-256 and AES-256-GCM using your password. It is never stored or sent in plaintext, and it cannot be recovered if you forget the password.</span>
              </div>
              <div className="row mt">
                {unlocked ? (
                  <Button icon={LockKeyhole} onClick={doLock}>
                    Lock vault now
                  </Button>
                ) : (
                  <Button variant="primary" icon={KeyRound} onClick={unlock}>
                    Unlock vault
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </SlideUp>
      </div>

      <SlideUp delay={0.1}>
        <Card className="mt">
          <CardHeader title="How your files are protected" />
          <div className="card-body">
            <Stagger className="grid grid-3">
              {LAYERS.map(([title, body]) => (
                <div key={title} className="callout">
                  <ShieldCheck size={18} aria-hidden="true" />
                  <span>
                    <strong style={{ color: 'var(--text)' }}>{title}</strong>
                    <br />
                    {body}
                  </span>
                </div>
              ))}
            </Stagger>
          </div>
        </Card>
      </SlideUp>
    </>
  )
}


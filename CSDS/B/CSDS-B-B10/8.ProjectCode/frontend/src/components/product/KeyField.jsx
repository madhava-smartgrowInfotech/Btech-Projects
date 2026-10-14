import { KeyRound } from 'lucide-react'
import { useState } from 'react'
import api, { describeError } from '../../api'
import { HEX64 } from '../../format'
import { Button, Input } from '../ui/controls'
import { ErrorState } from '../ui/feedback'

// 256-bit key in hex. `optional` lets an empty field mean "make a new key on the server".
// `allowNew` = false hides "New key" where a fresh key cannot help (decrypting an existing image).
export default function KeyField({ value, onChange, optional = false, allowNew = true, label = 'Key (64 hex characters)', id = 'key' }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const bad = value !== '' && !HEX64.test(value)

  async function newKey() {
    setBusy(true)
    setError(null)
    try {
      const r = await api.get('/keys/new')
      onChange(r.data.key)
    } catch (e) {
      setError(describeError(e, 'Could not make a key'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-2">
        <Input id={id} label={label} value={value} onChange={(e) => onChange(e.target.value.trim())}
          spellCheck={false} autoComplete="off" className="min-w-0 flex-1" maxLength={64}
          placeholder={optional ? 'empty = new random key' : '64 hex characters'}
          error={bad ? 'Needs exactly 64 hex characters (0-9, a-f)' : undefined} />
        {allowNew && <Button variant="secondary" icon={KeyRound} loading={busy} onClick={newKey} className="mb-px">New key</Button>}
      </div>
      {error && <ErrorState error={error} compact onRetry={newKey} />}
    </div>
  )
}

// True when the key can be sent: valid hex, or empty if the field is optional.
export function keyReady(value, optional = false) {
  return value === '' ? optional : HEX64.test(value)
}

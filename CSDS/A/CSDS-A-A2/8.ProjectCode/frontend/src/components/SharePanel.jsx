import { useState } from 'react'
import { Check, Copy, ExternalLink } from 'lucide-react'
import { sessionLink } from '../lib/api'
import { Button, useToast } from './ui'

/** Session link + copy button + QR code (same content as the Streamlit share block). */
export function SharePanel({ token, qr = true }) {
  const toast = useToast()
  const [copied, setCopied] = useState(false)
  const link = sessionLink(token)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link)
      setCopied(true)
      toast.success('Session link copied.')
      setTimeout(() => setCopied(false), 1800)
    } catch {
      toast.warning('Copy is blocked here — select the link and copy it manually.')
    }
  }

  return (
    <div className="stack" style={{ '--gap': '14px' }}>
      <div className="link-box">
        <code aria-label="Session link">{link}</code>
        <Button size="sm" variant="primary" icon={copied ? Check : Copy} onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <div className="row" style={{ alignItems: 'flex-start', '--gap': '20px' }}>
        {qr && <img className="qr" src={`/api/qr?text=${encodeURIComponent(link)}`} alt="QR code that opens the session link" width="200" height="200" />}
        <div className="stack" style={{ '--gap': '8px', flex: '1 1 200px' }}>
          <p className="small">Scan to open the session. Students sign in, verify location, pass a random live challenge and a face match.</p>
          <div>
            <Button size="sm" href={link} target="_blank" rel="noreferrer" icon={ExternalLink}>
              Open student view
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, LogIn } from 'lucide-react'
import { Alert, Button, Card, Container, Input } from '../components/ui'
import { MaskHeadline, PageTransition } from '../components/motion'
import { useAuth } from '../lib/auth'

/** Student portal: paste the session link or token (ui/student.render(None)). */
export default function CheckinPortal() {
  const nav = useNavigate()
  const { user } = useAuth()
  const [raw, setRaw] = useState('')
  const [error, setError] = useState('')

  const go = (e) => {
    e.preventDefault()
    const tok = raw.trim().split('session=').pop().split('&')[0].split('/').pop().trim()
    if (!tok) {
      setError('Paste the session link (or just its token) shared by your faculty.')
      return
    }
    nav(`/checkin/${encodeURIComponent(decodeURIComponent(tok))}`)
  }

  return (
    <PageTransition>
      <Container>
        <div className="auth-grid">
          <div>
            <span className="eyebrow">Student portal</span>
            <MaskHeadline className="display-xl" lines={['Check', 'in.']} />
            <p className="lead muted" style={{ marginTop: 20 }}>
              Open the session link shared by your faculty, or paste it here. You will sign in, confirm your location, take two photos for
              the live challenge, and your face is matched — all in under a minute.
            </p>
          </div>
          <Card>
            <form className="stack" onSubmit={go} noValidate>
              <Input
                label="Session link or token"
                placeholder="http://…/?session=AbC123…"
                value={raw}
                onChange={(e) => setRaw(e.target.value)}
                error={error}
                data-autofocus
              />
              <Button type="submit" variant="primary" size="lg" iconRight={ArrowRight} block>
                Open session
              </Button>
            </form>
            <div style={{ marginTop: 20 }}>
              {user ? (
                <Alert tone="info">
                  Signed in as {user.full_name}
                  {user.roll_number ? ` · ${user.roll_number}` : ''}.
                </Alert>
              ) : (
                <Button to="/login?role=student" icon={LogIn} variant="ghost">
                  Sign in first (optional)
                </Button>
              )}
            </div>
          </Card>
        </div>
      </Container>
    </PageTransition>
  )
}

import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, GraduationCap, LogOut, Presentation } from 'lucide-react'
import { Alert, Button, Card, Container, Tabs } from '../components/ui'
import { MaskHeadline, PageTransition } from '../components/motion'
import { LoginForm } from '../components/AuthForms'
import { useAuth } from '../lib/auth'

export default function Login() {
  const [params] = useSearchParams()
  const nav = useNavigate()
  const { user, logout } = useAuth()
  const [role, setRole] = useState(params.get('role') === 'student' ? 'student' : 'faculty')
  const next = params.get('next')

  const done = (u) => nav(next || (u.role === 'faculty' ? '/app' : '/checkin'))

  return (
    <PageTransition>
      <Container>
        <div className="auth-grid">
          <div>
            <span className="eyebrow">{role === 'faculty' ? 'Faculty portal' : 'Student portal'}</span>
            <MaskHeadline className="display-xl" lines={['Sign', 'in.']} />
            <p className="lead muted" style={{ marginTop: 20 }}>
              {role === 'faculty'
                ? 'Create geo-fenced sessions, watch check-ins arrive, and export the register to Excel.'
                : 'Sign in with your roll number, then open the session link your faculty shared to mark attendance.'}
            </p>
          </div>
          <Card>
            <Tabs
              label="Account type"
              value={role}
              onChange={setRole}
              tabs={[
                { id: 'faculty', label: 'Faculty', icon: Presentation },
                { id: 'student', label: 'Student', icon: GraduationCap },
              ]}
            />
            {user ? (
              <div className="stack">
                <Alert tone="success">
                  You are signed in as {user.full_name} ({user.role}
                  {user.roll_number ? ` · ${user.roll_number}` : ''}).
                </Alert>
                <div className="row">
                  <Button variant="primary" iconRight={ArrowRight} onClick={() => done(user)}>
                    Continue
                  </Button>
                  <Button icon={LogOut} onClick={logout}>
                    Sign out
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <LoginForm key={role} role={role} defaultUsername={params.get('username') || ''} onSuccess={done} />
                <p className="small" style={{ marginTop: 18 }}>
                  New here?{' '}
                  <Link to={`/register?role=${role}`} style={{ fontWeight: 700 }}>
                    Create a {role} account
                  </Link>
                </p>
              </>
            )}
          </Card>
        </div>
      </Container>
    </PageTransition>
  )
}

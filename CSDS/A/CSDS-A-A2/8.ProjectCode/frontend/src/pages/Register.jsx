import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { GraduationCap, Presentation } from 'lucide-react'
import { Card, Container, Tabs } from '../components/ui'
import { MaskHeadline, PageTransition } from '../components/motion'
import { RegisterForm } from '../components/AuthForms'

export default function Register() {
  const [params] = useSearchParams()
  const nav = useNavigate()
  const [role, setRole] = useState(params.get('role') === 'faculty' ? 'faculty' : 'student')
  const next = params.get('next')

  return (
    <PageTransition>
      <Container>
        <div className="auth-grid">
          <div>
            <span className="eyebrow">New account</span>
            <MaskHeadline className="display-xl" lines={['Join', 'the', 'register.']} />
            <p className="lead muted" style={{ marginTop: 20 }}>
              {role === 'student'
                ? 'Students enrol a reference face once. Every check-in is compared against it — and against every other face already recorded in that session.'
                : 'Faculty accounts create sessions, manage students and export attendance.'}
            </p>
          </div>
          <Card>
            <Tabs
              label="Account type"
              value={role}
              onChange={setRole}
              tabs={[
                { id: 'student', label: 'Student', icon: GraduationCap },
                { id: 'faculty', label: 'Faculty', icon: Presentation },
              ]}
            />
            <RegisterForm
              key={role}
              role={role}
              onRegistered={(u) => {
                const q = new URLSearchParams({ role, username: u.roll_number || u.username })
                if (next) q.set('next', next)
                nav(`/login?${q}`)
              }}
            />
            <p className="small" style={{ marginTop: 18 }}>
              Already registered?{' '}
              <Link to={`/login?role=${role}${next ? `&next=${encodeURIComponent(next)}` : ''}`} style={{ fontWeight: 700 }}>
                Sign in
              </Link>
            </p>
          </Card>
        </div>
      </Container>
    </PageTransition>
  )
}

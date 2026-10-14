import { Component, lazy, Suspense, useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { AppShell, Button, Container, ErrorState, PublicShell, SkeletonBlock } from './components/ui'
import { useLenis } from './components/motion'
import { useAuth } from './lib/auth'
import { ScrollTrigger } from './lib/gsap'

// Route-level code splitting: every screen is its own chunk.
const Landing = lazy(() => import('./pages/Landing'))
const About = lazy(() => import('./pages/About'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const CheckinPortal = lazy(() => import('./pages/CheckinPortal'))
const Checkin = lazy(() => import('./pages/Checkin'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Sessions = lazy(() => import('./pages/Sessions'))
const CreateSession = lazy(() => import('./pages/CreateSession'))
const SessionDetail = lazy(() => import('./pages/SessionDetail'))
const Students = lazy(() => import('./pages/Students'))
const NotFound = lazy(() => import('./pages/NotFound'))

class Boundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) {
    return { error }
  }
  componentDidUpdate(prev) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null })
  }
  render() {
    if (this.state.error) {
      return (
        <Container style={{ padding: '48px 16px' }}>
          <ErrorState title="This screen crashed" error={this.state.error} hint="Reload the page. If it happens again, note what you clicked." onRetry={() => window.location.reload()} />
        </Container>
      )
    }
    return this.props.children
  }
}

function PageFallback() {
  return (
    <Container style={{ padding: '40px 16px' }}>
      <SkeletonBlock rows={5} label="Loading screen" />
    </Container>
  )
}

function ScrollToTop() {
  const { pathname } = useLocation()
  const lenis = useLenis()
  useEffect(() => {
    if (lenis) lenis.scrollTo(0, { immediate: true })
    else window.scrollTo(0, 0)
    const t = setTimeout(() => ScrollTrigger.refresh(), 400)
    return () => clearTimeout(t)
  }, [pathname, lenis])
  return null
}

function RequireFaculty() {
  const { user, logout } = useAuth()
  const loc = useLocation()
  const nav = useNavigate()
  if (!user) return <Navigate to={`/login?role=faculty&next=${encodeURIComponent(loc.pathname)}`} replace />
  if (user.role !== 'faculty') {
    return (
      <PublicShell>
        <Container style={{ padding: '48px 16px' }}>
          <ErrorState
            title="Faculty portal"
            error="You are signed in as a student. Sign out to use the faculty portal."
            hint="Students mark attendance from the session link their faculty shares."
          />
          <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
            <Button
              icon={LogOut}
              onClick={async () => {
                await logout()
                nav('/login?role=faculty')
              }}
            >
              Sign out
            </Button>
          </div>
        </Container>
      </PublicShell>
    )
  }
  return (
    <AppShell>
      <Boundary resetKey={loc.pathname}>
        <Suspense fallback={<SkeletonBlock rows={6} label="Loading screen" />}>
          <Outlet />
        </Suspense>
      </Boundary>
    </AppShell>
  )
}

function PublicLayout() {
  const loc = useLocation()
  return (
    <PublicShell>
      <Boundary resetKey={loc.pathname}>
        <Suspense fallback={<PageFallback />}>
          <Outlet />
        </Suspense>
      </Boundary>
    </PublicShell>
  )
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/checkin" element={<CheckinPortal />} />
          <Route path="/checkin/:token" element={<Checkin />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="/app" element={<RequireFaculty />}>
          <Route index element={<Dashboard />} />
          <Route path="sessions" element={<Sessions />} />
          <Route path="sessions/new" element={<CreateSession />} />
          <Route path="sessions/:id" element={<SessionDetail />} />
          <Route path="students" element={<Students />} />
        </Route>
      </Routes>
    </>
  )
}

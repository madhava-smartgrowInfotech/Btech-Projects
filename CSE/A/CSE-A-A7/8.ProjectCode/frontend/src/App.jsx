import { Suspense, lazy } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { RequireAuth } from './lib/auth'
import { AppShell, Container, PublicShell, SkeletonBlock, EmptyState, Button } from './components/ui'
import { PageTransition } from './components/motion'
import { SearchX } from 'lucide-react'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const NewPatient = lazy(() => import('./pages/NewPatient'))
const PatientResult = lazy(() => import('./pages/PatientResult'))
const Queue = lazy(() => import('./pages/Queue'))
const Performance = lazy(() => import('./pages/Performance'))

const fallback = (
  <Container style={{ padding: '48px 16px' }}>
    <SkeletonBlock rows={5} label="Loading page" />
  </Container>
)

function NotFound() {
  return (
    <Container style={{ padding: '64px 16px' }}>
      <EmptyState icon={SearchX} title="Page not found" action={<Button variant="primary" to="/">Back to ATHENA</Button>}>
        That address does not exist.
      </EmptyState>
    </Container>
  )
}

function Protected({ children }) {
  return (
    <RequireAuth>
      <AppShell>
        <PageTransition>{children}</PageTransition>
      </AppShell>
    </RequireAuth>
  )
}

export default function App() {
  const loc = useLocation()
  return (
    <Suspense fallback={fallback}>
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={loc} key={loc.pathname.startsWith('/app') ? 'app' : loc.pathname}>
          <Route path="/" element={<PublicShell><Landing /></PublicShell>} />
          <Route path="/login" element={<PublicShell><Login /></PublicShell>} />
          <Route path="/app" element={<Protected><Queue /></Protected>} />
          <Route path="/app/queue" element={<Protected><Queue /></Protected>} />
          <Route path="/app/new" element={<Protected><NewPatient /></Protected>} />
          <Route path="/app/patients/:id" element={<Protected><PatientResult /></Protected>} />
          <Route path="/app/performance" element={<Protected><Performance /></Protected>} />
          <Route path="*" element={<PublicShell><NotFound /></PublicShell>} />
        </Routes>
      </AnimatePresence>
    </Suspense>
  )
}

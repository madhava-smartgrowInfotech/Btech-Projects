import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { SearchX } from 'lucide-react'
import { AppShell, Button, EmptyState, PageSkeleton } from './components/ui'

// Every screen is its own chunk so recharts / gsap only load when needed.
const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Verify = lazy(() => import('./pages/Verify'))
const Bulk = lazy(() => import('./pages/Bulk'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Models = lazy(() => import('./pages/Models'))
const Lab = lazy(() => import('./pages/Lab'))

function NotFound() {
  return (
    <div style={{ maxWidth: 560, margin: '80px auto', padding: '0 16px' }}>
      <EmptyState
        icon={SearchX}
        title="That page does not exist"
        message="The link may be old or mistyped."
        action={<Button to="/app">Go to the dashboard</Button>}
      />
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<div className="container" style={{ padding: '40px 16px' }}><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="verify" element={<Verify />} />
          <Route path="bulk" element={<Bulk />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="models" element={<Models />} />
          <Route path="lab" element={<Lab />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

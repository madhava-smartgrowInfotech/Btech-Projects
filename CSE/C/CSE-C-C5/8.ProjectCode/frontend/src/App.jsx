import { lazy, Suspense, useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import AppShell from './components/ui/AppShell'
import { Button } from './components/ui/controls'
import { EmptyState, PageSkeleton } from './components/ui/feedback'
import { logEvent } from './lib/activity'
import { Compass } from 'lucide-react'

const Landing = lazy(() => import('./pages/Landing'))
const Predict = lazy(() => import('./pages/Predict'))
const Recommend = lazy(() => import('./pages/Recommend'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Recruiter = lazy(() => import('./pages/Recruiter'))
const Companies = lazy(() => import('./pages/Companies'))

function NotFound() {
  return (
    <EmptyState icon={Compass} title="404 - no such screen" body="That address does not exist in this app."
      action={<Link to="/predict"><Button>Go to eligibility</Button></Link>} />
  )
}

// Moves focus + scroll to the top on navigation and records the visit in the activity log.
function RouteEffects() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
    logEvent('ui', `navigate ${pathname}`)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <>
      <RouteEffects />
      <Suspense fallback={<div className="p-8"><PageSkeleton /></div>}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route element={<AppShell />}>
            <Route path="/predict" element={<Predict />} />
            <Route path="/recommend" element={<Recommend />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/recruiter" element={<Recruiter />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  )
}

import { Suspense, lazy } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { AppShell, Button, EmptyState, PageSkeleton } from './components/ui'

const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Training = lazy(() => import('./pages/Training'))
const Unlearning = lazy(() => import('./pages/Unlearning'))
const Explorer = lazy(() => import('./pages/Explorer'))
const Audit = lazy(() => import('./pages/Audit'))

function NotFound() {
  return (
    <div className="container" style={{ padding: '80px 0' }}>
      <EmptyState icon={Compass} title="Page not found" message="That address does not exist in ForgetSafe." action={<Button to="/app">Go to dashboard</Button>} />
    </div>
  )
}

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="container" style={{ padding: '40px 0' }}>
          <PageSkeleton />
        </div>
      }
    >
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="training" element={<Training />} />
          <Route path="unlearning" element={<Unlearning />} />
          <Route path="explorer" element={<Explorer />} />
          <Route path="audit" element={<Audit />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

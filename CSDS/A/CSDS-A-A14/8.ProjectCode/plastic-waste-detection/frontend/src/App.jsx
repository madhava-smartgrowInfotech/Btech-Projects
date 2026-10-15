import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell, PageSkeleton } from './components/ui'
import Landing from './pages/Landing'
import NotFound from './pages/NotFound'

// Screens are code-split; the Dashboard also pulls in the chart library, so it loads on demand.
const Detection = lazy(() => import('./pages/Detection'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Evaluation = lazy(() => import('./pages/Evaluation'))
const About = lazy(() => import('./pages/About'))

const fallback = <PageSkeleton kpis={3} blocks={2} />

export default function App() {
  return (
    <Suspense fallback={fallback}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Navigate to="detect" replace />} />
          <Route path="detect" element={<Detection />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="evaluation" element={<Evaluation />} />
          <Route path="about" element={<About />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/ui/Layout'
import { PageSkeleton } from './components/ui/Feedback'

const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Plan = lazy(() => import('./pages/Plan'))
const Compare = lazy(() => import('./pages/Compare'))
const Rolling = lazy(() => import('./pages/Rolling'))
const Regions = lazy(() => import('./pages/Regions'))
const NotFound = lazy(() => import('./pages/NotFound'))

const page = (el) => <Suspense fallback={<PageSkeleton />}>{el}</Suspense>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Suspense fallback={null}><Landing /></Suspense>} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={page(<Dashboard />)} />
        <Route path="forecast" element={page(<Forecast />)} />
        <Route path="plan" element={page(<Plan />)} />
        <Route path="compare" element={page(<Compare />)} />
        <Route path="rolling" element={page(<Rolling />)} />
        <Route path="regions" element={page(<Regions />)} />
        <Route path="*" element={page(<NotFound />)} />
      </Route>
      <Route path="*" element={<Suspense fallback={null}><NotFound standalone /></Suspense>} />
    </Routes>
  )
}

import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell, Skeleton } from './components/ui'
import Landing from './pages/Landing'

const Overview = lazy(() => import('./pages/Overview'))
const Predict = lazy(() => import('./pages/Predict'))
const Models = lazy(() => import('./pages/Models'))
const Datasets = lazy(() => import('./pages/Datasets'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

function PageFallback() {
  return (
    <div className="container" aria-busy="true" aria-label="Loading page">
      <Skeleton height={34} width="40%" style={{ marginBottom: 18 }} />
      <Skeleton height={220} />
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Overview />} />
          <Route path="predict" element={<Navigate to="/app/predict/diabetes" replace />} />
          <Route path="predict/:disease" element={<Predict />} />
          <Route path="models" element={<Models />} />
          <Route path="data" element={<Datasets />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

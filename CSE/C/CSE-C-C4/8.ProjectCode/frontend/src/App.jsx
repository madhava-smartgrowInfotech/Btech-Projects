import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell, PageSkeleton } from './components/ui'

// Every screen is its own chunk, so charts and animation code load only when a screen is opened.
const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Models = lazy(() => import('./pages/Models'))
const Sentiment = lazy(() => import('./pages/Sentiment'))
const About = lazy(() => import('./pages/About'))

export default function App() {
  return (
    <Suspense fallback={<div className="container" style={{ padding: '40px 16px' }}><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="forecast" element={<Forecast />} />
          <Route path="models" element={<Models />} />
          <Route path="sentiment" element={<Sentiment />} />
          <Route path="about" element={<About />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

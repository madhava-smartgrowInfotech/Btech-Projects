import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { AppShell, PageSkeleton } from './components/ui'

const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Assess = lazy(() => import('./pages/Assess'))
const Result = lazy(() => import('./pages/Result'))
const Explain = lazy(() => import('./pages/Explain'))
const Forecast = lazy(() => import('./pages/Forecast'))
const WhatIf = lazy(() => import('./pages/WhatIf'))
const Performance = lazy(() => import('./pages/Performance'))
const About = lazy(() => import('./pages/About'))
const NotFound = lazy(() => import('./pages/NotFound'))

export default function App() {
  return (
    <Suspense fallback={<div className="container" style={{ paddingTop: 40 }}><PageSkeleton /></div>}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="assess" element={<Assess />} />
          <Route path="result" element={<Result />} />
          <Route path="explain" element={<Explain />} />
          <Route path="forecast" element={<Forecast />} />
          <Route path="whatif" element={<WhatIf />} />
          <Route path="performance" element={<Performance />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound standalone />} />
      </Routes>
    </Suspense>
  )
}

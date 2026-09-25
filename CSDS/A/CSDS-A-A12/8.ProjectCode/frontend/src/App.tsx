import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

const Landing = lazy(() => import('./pages/Landing').then((m) => ({ default: m.Landing })))
const Workspace = lazy(() => import('./pages/Workspace').then((m) => ({ default: m.Workspace })))
const History = lazy(() => import('./pages/History').then((m) => ({ default: m.History })))
const Insights = lazy(() => import('./pages/Insights').then((m) => ({ default: m.Insights })))

function PageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg)]">
      <div className="w-8 h-8 rounded-full border-2 border-emerald-500/30 border-t-emerald-400 animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Workspace />} />
          <Route path="/history" element={<History />} />
          <Route path="/insights" element={<Insights />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

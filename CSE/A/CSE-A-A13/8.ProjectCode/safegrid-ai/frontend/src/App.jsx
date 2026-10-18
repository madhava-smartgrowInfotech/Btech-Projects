import { lazy, Suspense } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { RequireAuth } from './lib/auth'
import { SimulationProvider } from './hooks/useSimulation'
import { AppShell } from './components/ui/layout'
import { EmptyState, Skeleton } from './components/ui/feedback'

const Landing = lazy(() => import('./pages/Landing'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const GridView = lazy(() => import('./pages/GridView'))
const AgentMonitor = lazy(() => import('./pages/AgentMonitor'))
const SafetyShield = lazy(() => import('./pages/SafetyShield'))
const PowerFlow = lazy(() => import('./pages/PowerFlow'))
const ScenarioRunner = lazy(() => import('./pages/ScenarioRunner'))
const Explainability = lazy(() => import('./pages/Explainability'))

function PageFallback() {
  return (
    <div className="stack" aria-busy="true" aria-label="Loading page" style={{ padding: 28 }}>
      <Skeleton width="40%" height={34} />
      <Skeleton height={140} radius={12} />
      <Skeleton height={260} radius={12} />
    </div>
  )
}

function NotFound() {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <EmptyState icon={Compass} title="Page not found" actions={<><Link className="btn btn-primary" to="/">Go to the landing page</Link><Link className="btn" to="/app">Open the console</Link></>}>
        That address does not exist in SafeGrid-AI.
      </EmptyState>
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <SimulationProvider>
                <AppShell />
              </SimulationProvider>
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="grid" element={<GridView />} />
          <Route path="agents" element={<AgentMonitor />} />
          <Route path="shield" element={<SafetyShield />} />
          <Route path="power-flow" element={<PowerFlow />} />
          <Route path="scenarios" element={<ScenarioRunner />} />
          <Route path="explain" element={<Explainability />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

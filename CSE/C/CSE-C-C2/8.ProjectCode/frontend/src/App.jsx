import { Component, lazy, Suspense } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { AppShell, EmptyState, ErrorState, PublicShell, SkeletonBlock, Button } from './components/ui'
import { PageTransition } from './components/motion'
import { Compass } from 'lucide-react'

// Pages are lazy so the landing page does not pay for Recharts or the studio code.
const Landing = lazy(() => import('./pages/Landing'))
const Studio = lazy(() => import('./pages/Studio'))
const History = lazy(() => import('./pages/History'))
const StoryDetail = lazy(() => import('./pages/StoryDetail'))
const Evaluation = lazy(() => import('./pages/Evaluation'))

class Boundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) {
    return { error }
  }
  render() {
    if (this.state.error) {
      return <ErrorState title="This screen crashed" error={this.state.error} hint="Reload the page. If it keeps happening, check the browser console." onRetry={() => window.location.reload()} />
    }
    return this.props.children
  }
}

const Loading = () => (
  <div className="container" style={{ padding: '40px 16px' }}>
    <SkeletonBlock rows={5} label="Loading screen" />
  </div>
)

function NotFound() {
  return (
    <EmptyState icon={Compass} title="Page not found" action={<Button variant="primary" to="/studio">Go to the studio</Button>}>
      That address does not exist in StoryVox.
    </EmptyState>
  )
}

function WithShell({ children }) {
  const { pathname } = useLocation()
  return (
    <AppShell>
      <Boundary key={pathname}>
        <PageTransition key={pathname}>{children}</PageTransition>
      </Boundary>
    </AppShell>
  )
}

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<PublicShell><Boundary><Landing /></Boundary></PublicShell>} />
        <Route path="/studio" element={<WithShell><Studio /></WithShell>} />
        <Route path="/stories" element={<WithShell><History /></WithShell>} />
        <Route path="/stories/:id" element={<WithShell><StoryDetail /></WithShell>} />
        <Route path="/evaluation" element={<WithShell><Evaluation /></WithShell>} />
        <Route path="*" element={<WithShell><NotFound /></WithShell>} />
      </Routes>
    </Suspense>
  )
}

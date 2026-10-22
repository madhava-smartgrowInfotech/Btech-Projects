import { Component, Suspense, lazy } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { AppShell, Button, Container, EmptyState, ErrorState, Skeleton } from './components/ui'

const Landing = lazy(() => import('./pages/Landing'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analyze = lazy(() => import('./pages/Analyze'))
const AnalysisDetail = lazy(() => import('./pages/AnalysisDetail'))
const Reviewers = lazy(() => import('./pages/Reviewers'))
const Model = lazy(() => import('./pages/Model'))
const History = lazy(() => import('./pages/History'))
const About = lazy(() => import('./pages/About'))

function PageFallback() {
  return (
    <Container>
      <div aria-busy="true" aria-label="Loading page" style={{ padding: '28px 0' }}>
        <Skeleton width={260} height={34} />
        <Skeleton height={14} width={420} style={{ marginTop: 14 }} />
        <Skeleton height={160} style={{ marginTop: 28 }} radius="18px" />
      </div>
    </Container>
  )
}

// A render error in one page must not blank the whole app.
class Boundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) {
    return { error }
  }
  componentDidUpdate(prev) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null })
  }
  render() {
    if (this.state.error) {
      return (
        <Container>
          <ErrorState title="This screen failed to render" error={this.state.error} onRetry={() => this.setState({ error: null })}>
            <p className="faint">Reload the page if it keeps happening.</p>
          </ErrorState>
        </Container>
      )
    }
    return this.props.children
  }
}

function NotFound() {
  return (
    <Container>
      <EmptyState
        icon={Compass}
        title="Page not found"
        actions={
          <>
            <Button as={Link} to="/app" variant="primary">
              Go to dashboard
            </Button>
            <Button as={Link} to="/">
              Landing page
            </Button>
          </>
        }
      >
        That address does not match any PeerScope screen.
      </EmptyState>
    </Container>
  )
}

export default function App() {
  const loc = useLocation()
  return (
    <Boundary resetKey={loc.pathname}>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="analyze" element={<Analyze />} />
            <Route path="analyses/:id" element={<AnalysisDetail />} />
            <Route path="reviewers" element={<Reviewers />} />
            <Route path="model" element={<Model />} />
            <Route path="history" element={<History />} />
            <Route path="about" element={<About />} />
            <Route path="*" element={<NotFound />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </Boundary>
  )
}

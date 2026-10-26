import { lazy, Suspense, useEffect } from 'react'
import { Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { ThemeProvider } from './lib/theme'
import { PipelineProvider } from './lib/pipeline'
import { SmoothScroll, PageTransition } from './components/motion'
import { AppShell, PublicShell, SkeletonBlock, ToastProvider } from './components/ui'

const Landing = lazy(() => import('./pages/Landing'))
const About = lazy(() => import('./pages/About'))
const Overview = lazy(() => import('./pages/Overview'))
const Upload = lazy(() => import('./pages/Upload'))
const Explore = lazy(() => import('./pages/Explore'))
const Demand = lazy(() => import('./pages/Demand'))
const Features = lazy(() => import('./pages/Features'))
const Training = lazy(() => import('./pages/Training'))
const Domain = lazy(() => import('./pages/Domain'))
const Evaluation = lazy(() => import('./pages/Evaluation'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Insights = lazy(() => import('./pages/Insights'))
const NotFound = lazy(() => import('./pages/NotFound'))

function Loading() {
  return (
    <div className="container" style={{ padding: '40px 16px' }}>
      <SkeletonBlock rows={4} label="Loading page" />
    </div>
  )
}

/** Move focus to the new page and reset scroll on navigation, so keyboard and screen-reader users start at the top. */
function RouteEffects() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
    document.getElementById('main')?.focus({ preventScroll: true })
  }, [pathname])
  return null
}

function AppLayout() {
  const { pathname } = useLocation()
  return (
    <AppShell>
      <PageTransition key={pathname}>
        <Outlet />
      </PageTransition>
    </AppShell>
  )
}

function PublicLayout() {
  return (
    <PublicShell>
      <Outlet />
    </PublicShell>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <SmoothScroll>
          <PipelineProvider>
            <RouteEffects />
            <Suspense fallback={<Loading />}>
              <Routes>
                <Route element={<PublicLayout />}>
                  <Route path="/" element={<Landing />} />
                  <Route path="/about" element={<About />} />
                </Route>
                <Route path="/app" element={<AppLayout />}>
                  <Route index element={<Overview />} />
                  <Route path="upload" element={<Upload />} />
                  <Route path="explore" element={<Explore />} />
                  <Route path="demand" element={<Demand />} />
                  <Route path="features" element={<Features />} />
                  <Route path="training" element={<Training />} />
                  <Route path="domain" element={<Domain />} />
                  <Route path="evaluation" element={<Evaluation />} />
                  <Route path="forecast" element={<Forecast />} />
                  <Route path="insights" element={<Insights />} />
                </Route>
                <Route element={<PublicLayout />}>
                  <Route path="*" element={<NotFound />} />
                </Route>
              </Routes>
            </Suspense>
          </PipelineProvider>
        </SmoothScroll>
      </ToastProvider>
    </ThemeProvider>
  )
}
